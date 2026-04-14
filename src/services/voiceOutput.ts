import { type ChildProcess, spawn, spawnSync } from 'child_process'
import { logForDebugging } from '../utils/debug.js'

const MAX_SPOKEN_CHARS = 1_200

let activeSpeaker: ChildProcess | null = null
const intentionallyStopped = new WeakSet<ChildProcess>()

function normalizeSpeechText(text: string): string {
  let cleaned = text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*>\s?/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/\r?\n{2,}/g, '. ')
    .replace(/\r?\n/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  if (!cleaned) {
    cleaned = text.replace(/`/g, '').replace(/\s+/g, ' ').trim()
  }

  if (cleaned.length <= MAX_SPOKEN_CHARS) {
    return cleaned
  }

  const clipped = cleaned.slice(0, MAX_SPOKEN_CHARS)
  const boundary = Math.max(
    clipped.lastIndexOf('. '),
    clipped.lastIndexOf('! '),
    clipped.lastIndexOf('? '),
    clipped.lastIndexOf('; '),
  )

  return (boundary > MAX_SPOKEN_CHARS * 0.6
    ? clipped.slice(0, boundary + 1)
    : clipped
  ).trim()
}

function getWindowsVoiceCommand(text: string): {
  command: string
  args: string[]
  env: NodeJS.ProcessEnv
} {
  const script = `
Add-Type -AssemblyName System.Speech
$encoded = $env:VOICE_REPLY_TEXT_BASE64
if ([string]::IsNullOrWhiteSpace($encoded)) { exit 0 }
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($encoded))
if ([string]::IsNullOrWhiteSpace($text)) { exit 0 }
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
  $speaker.Speak($text)
} finally {
  $speaker.Dispose()
}
`.trim()

  return {
    command: 'powershell',
    args: [
      '-NoProfile',
      '-NonInteractive',
      '-EncodedCommand',
      Buffer.from(script, 'utf16le').toString('base64'),
    ],
    env: {
      ...process.env,
      VOICE_REPLY_TEXT_BASE64: Buffer.from(text, 'utf8').toString('base64'),
    },
  }
}

function getUnixVoiceCommand(
  text: string,
): { command: string; args: string[]; env?: NodeJS.ProcessEnv } {
  if (process.platform === 'darwin') {
    return {
      command: 'say',
      args: [text],
    }
  }

  const spdSay = spawnSync('spd-say', ['--version'], {
    stdio: 'ignore',
    timeout: 1_500,
  })
  if (spdSay.error === undefined) {
    return {
      command: 'spd-say',
      args: [text],
    }
  }

  return {
    command: 'espeak',
    args: [text],
  }
}

function buildVoiceCommand(text: string): {
  command: string
  args: string[]
  env?: NodeJS.ProcessEnv
} {
  if (process.platform === 'win32') {
    return getWindowsVoiceCommand(text)
  }

  return getUnixVoiceCommand(text)
}

export function stopSpeaking(): void {
  if (!activeSpeaker) {
    return
  }

  intentionallyStopped.add(activeSpeaker)
  logForDebugging('[voice_output] Stopping active speech')
  activeSpeaker.kill()
  activeSpeaker = null
}

export async function speakText(rawText: string): Promise<void> {
  const text = normalizeSpeechText(rawText)
  if (!text) {
    logForDebugging('[voice_output] Nothing speakable after text cleanup')
    return
  }

  stopSpeaking()

  const { command, args, env } = buildVoiceCommand(text)
  logForDebugging(
    `[voice_output] Speaking ${String(text.length)} chars via ${command}`,
  )

  await new Promise<void>((resolve, reject) => {
    const child = spawn(command, args, {
      env,
      stdio: ['ignore', 'ignore', 'pipe'],
      windowsHide: true,
    })

    activeSpeaker = child

    child.once('error', error => {
      if (activeSpeaker === child) {
        activeSpeaker = null
      }
      reject(error)
    })

    child.stderr?.once('data', chunk => {
      logForDebugging(
        `[voice_output] stderr: ${chunk.toString().trim().slice(0, 200)}`,
      )
    })

    child.once('close', (code, signal) => {
      if (activeSpeaker === child) {
        activeSpeaker = null
      }

      if (intentionallyStopped.has(child)) {
        intentionallyStopped.delete(child)
        resolve()
        return
      }

      if (code === 0) {
        resolve()
        return
      }

      reject(
        new Error(
          `Voice output exited with code ${String(code)}${
            signal ? ` (${signal})` : ''
          }`,
        ),
      )
    })
  })
}
