import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell } from 'lucide-react'
import api from '../api/axios'
import socket from '../socket'
import { useAuth } from '../context/AuthContext'

function formatTime(isoString) {
  const date = new Date(isoString)
  return date.toLocaleTimeString('el-GR', { hour: '2-digit', minute: '2-digit' })
}

function ChatPage() {
  const [rooms, setRooms] = useState([])
  const [selectedRoom, setSelectedRoom] = useState(null)
  const [messages, setMessages] = useState([])
  const [messageText, setMessageText] = useState('')
  const [showInvite, setShowInvite] = useState(false)
  const [inviteUsername, setInviteUsername] = useState('')
  const [inviteError, setInviteError] = useState('')

  const [invitations, setInvitations] = useState([])
  const [showNotifications, setShowNotifications] = useState(false)

  const [toast, setToast] = useState(null)

  const showToast = (message) => {
    setToast(message)
    setTimeout(() => setToast(null), 3000)
  }

  const { token, logout } = useAuth()
  const navigate = useNavigate()

  const selectedRoomRef = useRef(null)
  useEffect(() => {
    selectedRoomRef.current = selectedRoom
  }, [selectedRoom])

  const fetchRooms = async () => {
    try {
      const response = await api.get('/rooms')
      setRooms(response.data)
    } catch (err) {
      console.error('Σφάλμα στη λήψη rooms:', err)
    }
  }

  useEffect(() => {
    fetchRooms()
  }, [])

  useEffect(() => {
    const fetchInvitations = async () => {
      try {
        const response = await api.get('/invitations')
        setInvitations(response.data)
      } catch (err) {
        console.error('Σφάλμα στη λήψη προσκλήσεων:', err)
      }
    }
    fetchInvitations()
  }, [])

  useEffect(() => {
    socket.auth = { token }
    socket.connect()

    socket.on('new_message', (data) => {
      if (data.room_id !== selectedRoomRef.current?.id) return
      setMessages((prev) => [...prev, data])
    })

    socket.on('new_invitation', (data) => {
      setInvitations((prev) => [...prev, data])
    })

    return () => {
      socket.off('new_message')
      socket.off('new_invitation')
      socket.disconnect()
    }
  }, [token])

  useEffect(() => {
    if (!selectedRoom) return

    const fetchMessages = async () => {
      try {
        const response = await api.get(`/rooms/${selectedRoom.id}/messages`)
        setMessages(response.data)
      } catch (err) {
        console.error('Σφάλμα στη λήψη μηνυμάτων:', err)
      }
    }
    fetchMessages()

    socket.emit('join_room', { room_id: selectedRoom.id })
  }, [selectedRoom])

  const handleSend = (e) => {
    e.preventDefault()
    if (!messageText.trim() || !selectedRoom) return

    socket.emit('send_message', {
      room_id: selectedRoom.id,
      text: messageText,
    })

    setMessageText('')
  }

  const handleInvite = async (e) => {
    e.preventDefault()
    setInviteError('')
    try {
      await api.post(`/rooms/${selectedRoom.id}/members`, { username: inviteUsername })
      showToast(`Η πρόσκληση στάλθηκε στον ${inviteUsername}`)
      setInviteUsername('')
      setShowInvite(false)
    } catch (err) {
      setInviteError(err.response?.data?.error || 'Κάτι πήγε στραβά')
    }
  }

  const handleAcceptInvitation = async (invitationId) => {
    try {
      await api.post(`/invitations/${invitationId}/accept`)
      setInvitations((prev) => prev.filter((inv) => inv.id !== invitationId))
      fetchRooms()
      setShowNotifications(false)
    } catch (err) {
      console.error('Σφάλμα αποδοχής:', err)
    }
  }

  const handleRejectInvitation = async (invitationId) => {
    try {
      await api.post(`/invitations/${invitationId}/reject`)
      setInvitations((prev) => prev.filter((inv) => inv.id !== invitationId))
    } catch (err) {
      console.error('Σφάλμα απόρριψης:', err)
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex bg-bg-main">
      {/* Sidebar */}
      <div className="w-64 bg-bg-sidebar border-r border-border flex flex-col">
        <div className="p-4 border-b border-border flex items-center justify-between relative">
          <h2 className="text-text-header font-bold">Rooms</h2>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowNotifications((prev) => !prev)}
              className="text-text-secondary hover:text-accent relative"
            >
              <Bell size={20} />
              {invitations.length > 0 && (
                <span className="absolute -top-1.5 -right-1.5 bg-red-500 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
                  {invitations.length}
                </span>
              )}
            </button>

            <button onClick={handleLogout} className="text-text-secondary text-xs hover:text-accent">
              Logout
            </button>
          </div>

          {showNotifications && (
            <div className="absolute left-4 top-14 w-64 bg-bg-elevated border border-border rounded shadow-lg z-10">
              {invitations.length === 0 ? (
                <p className="text-text-secondary text-sm p-3">Καμία πρόσκληση</p>
              ) : (
                invitations.map((inv) => (
                  <div key={inv.id} className="p-3 border-b border-border last:border-b-0">
                    <p className="text-text-primary text-sm">
                      <span className="font-semibold">{inv.invited_by}</span> σε προσκάλεσε στο{' '}
                      <span className="font-semibold"># {inv.room_name}</span>
                    </p>
                    <div className="flex gap-2 mt-2">
                      <button
                        onClick={() => handleAcceptInvitation(inv.id)}
                        className="bg-accent hover:bg-accent-hover text-white text-xs px-2 py-1 rounded"
                      >
                        Αποδοχή
                      </button>
                      <button
                        onClick={() => handleRejectInvitation(inv.id)}
                        className="text-text-secondary hover:text-red-400 text-xs px-2 py-1 rounded border border-border"
                      >
                        Απόρριψη
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        <div className="flex-1 overflow-y-auto">
          {rooms.map((room) => (
            <button
              key={room.id}
              onClick={() => setSelectedRoom(room)}
              className={`w-full text-left px-4 py-2 text-text-primary hover:bg-bg-elevated ${
                selectedRoom?.id === room.id ? 'bg-bg-elevated' : ''
              }`}
            >
              # {room.name}
            </button>
          ))}
        </div>
      </div>

      {/* Κυρίως χώρος */}
      <div className="flex-1 flex flex-col">
        {selectedRoom ? (
          <>
            <div className="p-4 border-b border-border flex items-center justify-between relative">
              <h2 className="text-text-header font-bold"># {selectedRoom.name}</h2>

              {showInvite ? (
                <div>
                  <form onSubmit={handleInvite} className="flex gap-2">
                    <input
                      type="text"
                      value={inviteUsername}
                      onChange={(e) => setInviteUsername(e.target.value)}
                      placeholder="username"
                      autoFocus
                      className="bg-bg-elevated text-text-primary text-sm rounded p-1.5 outline-none border border-border focus:border-accent"
                    />
                    <button type="submit" className="bg-accent hover:bg-accent-hover text-white text-sm px-3 py-1.5 rounded">
                      Πρόσκληση
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setShowInvite(false)
                        setInviteError('')
                      }}
                      className="text-text-secondary text-sm hover:text-accent"
                    >
                      Ακύρωση
                    </button>
                  </form>
                  {inviteError && (
                    <p className="text-red-400 text-xs mt-1">{inviteError}</p>
                  )}
                </div>
              ) : (
                <button
                  onClick={() => setShowInvite(true)}
                  className="text-text-secondary text-sm hover:text-accent"
                >
                  + Πρόσκληση
                </button>
              )}

              {toast && (
                <div className="absolute right-4 top-14 bg-bg-elevated border border-border text-text-primary text-sm px-4 py-3 rounded shadow-lg">
                  {toast}
                </div>
              )}
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {messages.map((msg) => (
                <div key={msg.id} className="flex gap-3 py-1.5 px-2 rounded hover:bg-bg-elevated/40">
                  <div className="w-10 h-10 rounded-full bg-accent flex items-center justify-center text-white font-bold shrink-0">
                    {msg.username.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-text-header font-semibold">{msg.username}</span>
                      <span className="text-text-secondary text-xs">{formatTime(msg.created_at)}</span>
                    </div>
                    <p className="text-text-primary">{msg.text}</p>
                  </div>
                </div>
              ))}
            </div>

            <form onSubmit={handleSend} className="p-4 border-t border-border flex gap-2">
              <input
                type="text"
                value={messageText}
                onChange={(e) => setMessageText(e.target.value)}
                placeholder="Γράψε μήνυμα..."
                className="flex-1 bg-bg-elevated text-text-primary rounded p-2 outline-none border border-border focus:border-accent"
              />
              <button type="submit" className="bg-accent hover:bg-accent-hover text-white px-4 py-2 rounded">
                Αποστολή
              </button>
            </form>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-text-secondary">Επίλεξε ένα room από αριστερά</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatPage