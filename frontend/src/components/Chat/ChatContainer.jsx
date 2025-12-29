import { useAtomValue } from 'jotai';
import { useEffect, useRef } from 'react';
import { messagesAtom } from '../../atom/messageAtom';
import './Chat.css';
import Message from './Message';

function ChatContainer({ isLoading, onSendMessage }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const messages = useAtomValue(messagesAtom);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="chat-container">
      <div className="messages-wrapper">
        {messages?.map((message, index) => (
          <Message key={index} message={message} onSendMessage={onSendMessage} />
        ))}
        {isLoading && (
          <div className="loading-indicator">
            <div className="typing-dots">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}

export default ChatContainer;