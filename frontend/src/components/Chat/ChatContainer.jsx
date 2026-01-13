import { useAtomValue } from 'jotai';
import { useEffect, useRef, useState } from 'react';
import { messagesAtom } from '../../atom/messageAtom';
import './Chat.css';
import Message from './Message';

function ChatContainer({ isLoading, onSendMessage }) {

  const messages = useAtomValue(messagesAtom);
  const [showThinkingText, setShowThinkingText] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    let timer;
    if (isLoading) {
      setShowThinkingText(false);
      timer = setTimeout(() => {
        setShowThinkingText(true);
      }, 8000);
    } else {
      setShowThinkingText(false);
    }
    
    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [isLoading]);

  return (
    <div className="chat-container">
      <div className="messages-wrapper">
        {messages?.map((message, index) => (
          <Message key={index} message={message} onSendMessage={onSendMessage} typing={index === messages.length - 1 && index !== 0 && !message.view_history} />
        ))}
        {isLoading && (
          <div className="loading-indicator">
            <div className="typing-dots">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
            {showThinkingText && (
              <span className="thinking-text">đang suy nghĩ...</span>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>  
  );
}

export default ChatContainer;