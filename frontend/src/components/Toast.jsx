import React, { useEffect, useState } from 'react'
import './Toast.css'

let toastId = 0
const toasts = []
const listeners = []

function notifyListeners() {
  listeners.forEach(listener => listener([...toasts]))
}

export function showToast(message, type = 'info', duration = 3000) {
  const id = toastId++
  const toast = { id, message, type, duration }
  toasts.push(toast)
  notifyListeners()

  if (duration > 0) {
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  return id
}

export function removeToast(id) {
  const index = toasts.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.splice(index, 1)
    notifyListeners()
  }
}

export function ToastContainer() {
  const [toastList, setToastList] = useState([])

  useEffect(() => {
    const listener = (newToasts) => {
      setToastList(newToasts)
    }
    listeners.push(listener)
    setToastList([...toasts])

    return () => {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [])

  return (
    <div className="toast-container">
      {toastList.map(toast => (
        <div
          key={toast.id}
          className={`toast toast-${toast.type}`}
          onClick={() => removeToast(toast.id)}
        >
          <span className="toast-icon">
            {toast.type === 'success' && '✅'}
            {toast.type === 'error' && '❌'}
            {toast.type === 'warning' && '⚠️'}
            {toast.type === 'info' && 'ℹ️'}
          </span>
          <span className="toast-message">{toast.message}</span>
          <button className="toast-close" onClick={() => removeToast(toast.id)}>
            ×
          </button>
        </div>
      ))}
    </div>
  )
}

