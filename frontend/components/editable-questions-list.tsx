import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { PlusCircle } from "lucide-react";
import { Label } from "@/components/ui/label";

interface EditableQuestionsListProps {
  questions: string[];
  answers: string[];
  onQAChange: (updatedQuestions: string[], updatedAnswers: string[]) => void;
}

export default function EditableQuestionsList({
  questions,
  answers,
  onQAChange,
}: EditableQuestionsListProps) {
  // Local copies for editing
  const [editingQuestions, setEditingQuestions] = useState<string[]>([...questions]);
  const [editingAnswers, setEditingAnswers] = useState<string[]>([...answers]);

  // Sync local state with props when they change (e.g., after a router.refresh())
  useEffect(() => {
    setEditingQuestions([...questions]);
    setEditingAnswers([...answers]);
  }, [questions, answers]);

  const handleQuestionChange = (index: number, value: string) => {
    const updated = [...editingQuestions];
    updated[index] = value;
    setEditingQuestions(updated);
    onQAChange(updated, editingAnswers);
  };

  const handleAnswerChange = (index: number, value: string) => {
    const updated = [...editingAnswers];
    updated[index] = value;
    setEditingAnswers(updated);
    onQAChange(editingQuestions, updated);
  };

  const handleAddQA = () => {
    const updatedQ = [...editingQuestions, ""];
    const updatedA = [...editingAnswers, ""];
    setEditingQuestions(updatedQ);
    setEditingAnswers(updatedA);
    onQAChange(updatedQ, updatedA);
  };

  return (
    <div className="space-y-6">
      {editingQuestions.map((q, index) => (
        <div key={index} className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor={`question-${index}`}>{`Question ${index + 1}`}</Label>
            <Textarea
              id={`question-${index}`}
              value={q}
              onChange={(e) => handleQuestionChange(index, e.target.value)}
              placeholder="Enter question..."
              rows={2}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor={`answer-${index}`}>{`Answer ${index + 1}`}</Label>
            <Textarea
              id={`answer-${index}`}
              value={editingAnswers[index] || ""}
              onChange={(e) => handleAnswerChange(index, e.target.value)}
              placeholder="Enter answer..."
            />
          </div>
        </div>
      ))}

      <Button type="button" className="flex gap-2 items-center" onClick={handleAddQA}>
        <PlusCircle size={16} /> Add Q&A Pair
      </Button>
    </div>
  );
} 