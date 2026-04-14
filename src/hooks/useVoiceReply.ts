import { useEffect, useRef } from 'react'
import { useNotifications } from '../context/notifications.js'
import { useVoiceState } from '../context/voice.js'
import { speakText, stopSpeaking } from '../services/voiceOutput.js'
import { useAppState } from '../state/AppState.js'
import type { Message } from '../types/message.js'
import { toError } from '../utils/errors.js'
import { logError } from '../utils/log.js'
import { getContentText } from '../utils/messages.js'

type Args = {
  isLoading: boolean
  messages: Message[]
}

function getLatestAssistantTextMessage(messages: Message[]): Message | null {
  for (let index = messages.length - 1; index >= 0; index--) {
    const message = messages[index]
    if (message?.type !== 'assistant') {
      continue
    }

    const text = getContentText(message.message.content)
    if (text) {
      return message
    }
  }

  return null
}

export function useVoiceReply({ isLoading, messages }: Args): void {
  const voiceEnabled = useAppState(s => s.settings.voiceEnabled === true)
  const voiceReplyEnabled = useAppState(
    s => s.settings.voiceReplyEnabled !== false,
  )
  const voiceState = useVoiceState(s => s.voiceState)
  const { addNotification } = useNotifications()

  const initializedRef = useRef(false)
  const lastSpokenUuidRef = useRef<string | null>(null)
  const reportedErrorRef = useRef(false)

  const latestAssistant = getLatestAssistantTextMessage(messages)
  const latestAssistantUuid = latestAssistant?.uuid ?? null

  useEffect(() => {
    if (voiceState === 'recording' || isLoading) {
      stopSpeaking()
    }
  }, [voiceState, isLoading])

  useEffect(() => {
    return () => {
      stopSpeaking()
    }
  }, [])

  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true
      lastSpokenUuidRef.current = latestAssistantUuid
      return
    }

    if (!voiceEnabled || !voiceReplyEnabled) {
      lastSpokenUuidRef.current = latestAssistantUuid
      stopSpeaking()
      return
    }

    if (isLoading || !latestAssistant || !latestAssistantUuid) {
      return
    }

    if (latestAssistantUuid === lastSpokenUuidRef.current) {
      return
    }

    lastSpokenUuidRef.current = latestAssistantUuid
    const text = getContentText(latestAssistant.message.content)
    if (!text) {
      return
    }

    void speakText(text).catch(error => {
      logError(toError(error))
      if (reportedErrorRef.current) {
        return
      }
      reportedErrorRef.current = true
      addNotification({
        key: 'voice-output-error',
        text:
          "Couldn't start spoken replies on this machine. Voice dictation still works.",
        color: 'warning',
        priority: 'high',
        timeoutMs: 8_000,
      })
    })
  }, [
    addNotification,
    isLoading,
    latestAssistant,
    latestAssistantUuid,
    voiceEnabled,
    voiceReplyEnabled,
  ])
}
