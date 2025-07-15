import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { ApiService, ChatRefinementRequest, ChatMessage, MultipleChoiceQuestion, UserAnswer } from "@/lib/api";
import { toast } from "sonner";
import MultipleChoiceQuestions from "./multiple-choice-questions";

interface DfdChatProps {
  initialDfd: string;
  onComplete: (dfd: string, questions: string[], answers: string[]) => void;
}

export default function DfdChat({ initialDfd, onComplete }: DfdChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentInput, setCurrentInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);
  const [currentQuestions, setCurrentQuestions] = useState<MultipleChoiceQuestion[]>([]);
  const [multipleChoiceAnswers, setMultipleChoiceAnswers] = useState<UserAnswer[]>([]);
  const [showMultipleChoice, setShowMultipleChoice] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const onCompleteRef = useRef(onComplete);
  const hasInitialized = useRef(false);
  
  // Update the ref when onComplete changes
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize with first LLM question
  useEffect(() => {
    // Prevent double initialization due to React Strict Mode
    if (hasInitialized.current) {
      return;
    }
    hasInitialized.current = true;

    const initializeChat = async () => {
      setIsLoading(true);
      try {
        const request: ChatRefinementRequest = {
          textual_dfd: initialDfd,
          conversation_history: [],
          structured_answers: [],
        };
        const response = await ApiService.chatRefine(request);
        
        if (response.status === "need_more_info") {
          const assistantMessage: ChatMessage = {
            role: "assistant",
            content: response.assistant_response,
            timestamp: new Date().toISOString(),
          };
          setMessages([assistantMessage]);
          setConversationHistory([assistantMessage]);
          
          // Handle multiple choice questions if present
          if (response.multiple_choice_questions && response.multiple_choice_questions.length > 0) {
            setCurrentQuestions(response.multiple_choice_questions);
            setShowMultipleChoice(true);
          } else {
            setShowMultipleChoice(false);
          }
        } else if (response.status === "success") {
          onCompleteRef.current(initialDfd, response.questions, response.answers);
        }
      } catch (error) {
        toast.error("Failed to initialize chat");
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeChat();
  }, [initialDfd]); // Removed onComplete from dependencies since initialization should only happen once

  const handleSendMessage = async () => {
    if (!currentInput.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      role: "user",
      content: currentInput,
      timestamp: new Date().toISOString(),
    };

    const newMessages = [...messages, userMessage];
    const newConversationHistory = [...conversationHistory, userMessage];
    
    setMessages(newMessages);
    setConversationHistory(newConversationHistory);
    setCurrentInput("");
    setIsLoading(true);

    try {
      const request: ChatRefinementRequest = {
        textual_dfd: initialDfd,
        conversation_history: newConversationHistory,
        structured_answers: [], // Could be accumulated from previous rounds
        multiple_choice_answers: multipleChoiceAnswers,
      };

      const response = await ApiService.chatRefine(request);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.assistant_response,
        timestamp: new Date().toISOString(),
      };

      const updatedMessages = [...newMessages, assistantMessage];
      const updatedConversation = [...newConversationHistory, assistantMessage];
      
      setMessages(updatedMessages);
      setConversationHistory(updatedConversation);
      
      // Handle multiple choice questions if present
      if (response.multiple_choice_questions && response.multiple_choice_questions.length > 0) {
        setCurrentQuestions(response.multiple_choice_questions);
        setShowMultipleChoice(true);
        setMultipleChoiceAnswers([]); // Reset answers for new questions
      } else {
        setShowMultipleChoice(false);
      }

      if (response.status === "success") {
        // Show completion message and then transition
        setTimeout(() => {
          onCompleteRef.current(initialDfd, response.questions, response.answers);
        }, 2000); // Give user time to read final message
      }
    } catch (error) {
      toast.error("Failed to send message");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleMultipleChoiceAnswersChange = (answers: UserAnswer[]) => {
    setMultipleChoiceAnswers(answers);
  };

  const handleMultipleChoiceSubmit = async () => {
    if (multipleChoiceAnswers.length === 0) return;

    setIsLoading(true);
    setShowMultipleChoice(false);

    try {
      // Create a synthetic user message showing the choices made
      const choicesText = multipleChoiceAnswers.map(answer => {
        if (answer.custom_answer) {
          return `${answer.question_id}: ${answer.custom_answer}`;
        } else if (answer.selected_option_id) {
          const question = currentQuestions.find(q => q.id === answer.question_id);
          const option = question?.options.find(o => o.id === answer.selected_option_id);
          return `${answer.question_id}: ${option?.text || answer.selected_option_id}`;
        }
        return "";
      }).filter(Boolean).join("\n");

      const userMessage: ChatMessage = {
        role: "user",
        content: `Selected answers:\n${choicesText}`,
        timestamp: new Date().toISOString(),
      };

      const newMessages = [...messages, userMessage];
      const newConversationHistory = [...conversationHistory, userMessage];
      
      setMessages(newMessages);
      setConversationHistory(newConversationHistory);

      const request: ChatRefinementRequest = {
        textual_dfd: initialDfd,
        conversation_history: newConversationHistory,
        structured_answers: [],
        multiple_choice_answers: multipleChoiceAnswers,
      };

      const response = await ApiService.chatRefine(request);

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response.assistant_response,
        timestamp: new Date().toISOString(),
      };

      const updatedMessages = [...newMessages, assistantMessage];
      const updatedConversation = [...newConversationHistory, assistantMessage];
      
      setMessages(updatedMessages);
      setConversationHistory(updatedConversation);
      
      // Handle multiple choice questions if present
      if (response.multiple_choice_questions && response.multiple_choice_questions.length > 0) {
        setCurrentQuestions(response.multiple_choice_questions);
        setShowMultipleChoice(true);
        setMultipleChoiceAnswers([]); // Reset answers for new questions
      } else {
        setShowMultipleChoice(false);
      }

      if (response.status === "success") {
        setTimeout(() => {
          onCompleteRef.current(initialDfd, response.questions, response.answers);
        }, 2000);
      }
    } catch (error) {
      toast.error("Failed to send answers");
      console.error(error);
      setShowMultipleChoice(true); // Show questions again on error
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] border rounded-lg">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <Card className={`max-w-[80%] ${message.role === "user" ? "bg-blue-50" : "bg-gray-50"}`}>
              <CardContent className="p-3">
                <div className="text-sm text-gray-600 mb-1">
                  {message.role === "user" ? "You" : "ML Security Assistant"}
                </div>
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.timestamp && (
                  <div className="text-xs text-gray-400 mt-2">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <Card className="bg-gray-50">
              <CardContent className="p-3">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin h-4 w-4 border-2 border-gray-300 border-t-gray-600 rounded-full"></div>
                  <span className="text-sm text-gray-600">ML Security Assistant is analyzing...</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Multiple Choice Questions */}
      {showMultipleChoice && (
        <div className="border-t p-4">
          <MultipleChoiceQuestions
            questions={currentQuestions}
            onAnswersChange={handleMultipleChoiceAnswersChange}
            onSubmit={handleMultipleChoiceSubmit}
            isLoading={isLoading}
          />
        </div>
      )}

      {/* Regular Text Input */}
      {!showMultipleChoice && (
        <div className="border-t p-4">
          <div className="flex space-x-2">
            <Textarea
              value={currentInput}
              onChange={(e) => setCurrentInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your response about your ML system's security..."
              className="flex-1 min-h-[60px]"
              disabled={isLoading}
            />
            <Button onClick={handleSendMessage} disabled={isLoading || !currentInput.trim()}>
              Send
            </Button>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      )}
    </div>
  );
} 