import { useState, useEffect, useRef, useCallback } from 'react';
import {
  ChatMessage,
  getGroupMessages,
  sendGroupMessage,
  markGroupMessagesRead,
  getDirectMessages,
  sendDirectMessage,
  markDirectMessagesRead,
} from '../util/api';
import './GroupChat.css';

interface GroupMember {
  userId: number;
  name: string;
}

interface Props {
  groupId: number;
  groupName: string;
  members: GroupMember[];   // other members (not current user)
  currentUserId: number;
}

type ConversationKey = 'group' | number; // 'group' or a user ID

export default function GroupChat({ groupId, groupName, members, currentUserId }: Props) {
  const [open, setOpen]             = useState(false);
  const [active, setActive]         = useState<ConversationKey>('group');
  const [messages, setMessages]     = useState<ChatMessage[]>([]);
  const [input, setInput]           = useState('');
  const [sending, setSending]       = useState(false);
  const [unread, setUnread]         = useState<Record<ConversationKey, number>>({});
  const bottomRef                   = useRef<HTMLDivElement>(null);
  const pollRef                     = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── fetch messages for the active conversation ─────────────────────────────
  const fetchMessages = useCallback(async () => {
    try {
      const res = active === 'group'
        ? await getGroupMessages(groupId)
        : await getDirectMessages(active as number);
      if (res.ok) {
        const data: ChatMessage[] = await res.json();
        setMessages(data);
      }
    } catch {
      // silently swallow network errors during polling
    }
  }, [active, groupId]);

  // ── mark read when conversation is open ───────────────────────────────────
  const markRead = useCallback(async () => {
    try {
      if (active === 'group') {
        await markGroupMessagesRead(groupId);
      } else {
        await markDirectMessagesRead(active as number);
      }
      setUnread(prev => ({ ...prev, [active]: 0 }));
    } catch {
      // ignore
    }
  }, [active, groupId]);

  // ── poll every 4 s while chat is open ─────────────────────────────────────
  useEffect(() => {
    if (!open) {
      if (pollRef.current) clearInterval(pollRef.current);
      return;
    }
    fetchMessages();
    markRead();
    pollRef.current = setInterval(fetchMessages, 4000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [open, fetchMessages, markRead]);

  // ── reset messages + refetch when switching conversation ──────────────────
  useEffect(() => {
    setMessages([]);
    if (open) {
      fetchMessages();
      markRead();
    }
  }, [active]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── scroll to bottom on new messages ──────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── send ──────────────────────────────────────────────────────────────────
  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || sending) return;
    setSending(true);
    try {
      const res = active === 'group'
        ? await sendGroupMessage(groupId, trimmed)
        : await sendDirectMessage(active as number, trimmed);
      if (res.ok) {
        setInput('');
        fetchMessages();
      }
    } catch {
      // show nothing — retry on next poll
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const activeName = active === 'group'
    ? groupName
    : members.find(m => m.userId === active)?.name ?? 'Member';

  // total unread badge on the toggle button
  const totalUnread = Object.values(unread).reduce((s, n) => s + n, 0);

  return (
    <>
      {/* ── Floating toggle button ─────────────────────────────────────── */}
      <button
        className="gc-fab"
        onClick={() => setOpen(o => !o)}
        aria-label="Toggle group chat"
      >
        <span className="gc-fab__icon">{open ? '✕' : (
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        )}</span>
        {!open && totalUnread > 0 && (
          <span className="gc-fab__badge">{totalUnread > 9 ? '9+' : totalUnread}</span>
        )}
      </button>

      {/* ── Chat popup ────────────────────────────────────────────────── */}
      {open && (
        <div className="gc-popup">
          {/* Sidebar */}
          <aside className="gc-sidebar">
            <p className="gc-sidebar__heading">Chats</p>

            <button
              className={`gc-conv ${active === 'group' ? 'gc-conv--active' : ''}`}
              onClick={() => setActive('group')}
            >
              <span className="gc-conv__icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
              </span>
              <span className="gc-conv__name">{groupName}</span>
              {(unread['group'] ?? 0) > 0 && (
                <span className="gc-conv__badge">{unread['group']}</span>
              )}
            </button>

            <p className="gc-sidebar__subheading">Direct</p>
            {members.map(m => (
              <button
                key={m.userId}
                className={`gc-conv ${active === m.userId ? 'gc-conv--active' : ''}`}
                onClick={() => setActive(m.userId)}
              >
                <span className="gc-conv__avatar">
                  {m.name.charAt(0).toUpperCase()}
                </span>
                <span className="gc-conv__name">{m.name}</span>
                {(unread[m.userId] ?? 0) > 0 && (
                  <span className="gc-conv__badge">{unread[m.userId]}</span>
                )}
              </button>
            ))}
          </aside>

          {/* Main chat area */}
          <div className="gc-main">
            {/* Header */}
            <div className="gc-header">
              <span className="gc-header__title">{activeName}</span>
              <span className="gc-header__sub">
                {active === 'group' ? `${members.length + 1} members` : 'Direct message'}
              </span>
            </div>

            {/* Messages */}
            <div className="gc-messages">
              {messages.length === 0 && (
                <p className="gc-empty">No messages yet. Say hi!</p>
              )}
              {messages.map((msg, i) => {
                const isMine = msg.sender_id === currentUserId;
                const showName = !isMine && (i === 0 || messages[i - 1].sender_id !== msg.sender_id);
                return (
                  <div key={msg.id} className={`gc-bubble-row ${isMine ? 'gc-bubble-row--mine' : ''}`}>
                    {showName && (
                      <span className="gc-bubble__sender">{msg.sender_name}</span>
                    )}
                    <div className={`gc-bubble ${isMine ? 'gc-bubble--mine' : 'gc-bubble--theirs'}`}>
                      {msg.content}
                      <span className="gc-bubble__time">
                        {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                );
              })}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="gc-input-row">
              <textarea
                className="gc-input"
                rows={1}
                placeholder="Type a message…"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <button
                className="gc-send"
                onClick={handleSend}
                disabled={sending || !input.trim()}
                aria-label="Send message"
              >
                ➤
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
