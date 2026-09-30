import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
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
  const { token, logout } = useAuth()
  const navigate = useNavigate()

  const selectedRoomRef = useRef(null)
  useEffect(() => {
    selectedRoomRef.current = selectedRoom
  }, [selectedRoom])

  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const response = await api.get('/rooms')
        setRooms(response.data)
      } catch (err) {
        console.error('Σφάλμα στη λήψη rooms:', err)
      }
    }
    fetchRooms()
  }, [])

  useEffect(() => {
    socket.auth = { token }
    socket.connect()

    socket.on('new_message', (data) => {
      if (data.room_id !== selectedRoomRef.current?.id) return
      setMessages((prev) => [...prev, data])
    })

    return () => {
      socket.off('new_message')
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
      setInviteUsername('')
      setShowInvite(false)
    } catch (err) {
      setInviteError(err.response?.data?.error || 'Κάτι πήγε στραβά')
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
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h2 className="text-text-header font-bold">Rooms</h2>
          <button onClick={handleLogout} className="text-text-secondary text-xs hover:text-accent">
            Logout
          </button>
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
            <div className="p-4 border-b border-border flex items-center justify-between">
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