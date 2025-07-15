import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Edit2, Save, X } from "lucide-react";
import { MultipleChoiceQuestion, MultipleChoiceOption, UserAnswer } from "@/lib/api";

interface MultipleChoiceQuestionsProps {
  questions: MultipleChoiceQuestion[];
  onAnswersChange: (answers: UserAnswer[]) => void;
  onSubmit: () => void;
  isLoading?: boolean;
}

export default function MultipleChoiceQuestions({
  questions,
  onAnswersChange,
  onSubmit,
  isLoading = false
}: MultipleChoiceQuestionsProps) {
  const [answers, setAnswers] = useState<UserAnswer[]>([]);
  const [editingOptions, setEditingOptions] = useState<{ [questionId: string]: boolean }>({});
  const [tempOptions, setTempOptions] = useState<{ [questionId: string]: MultipleChoiceOption[] }>({});

  const updateAnswer = (questionId: string, update: Partial<UserAnswer>) => {
    const newAnswers = [...answers];
    const existingIndex = newAnswers.findIndex(a => a.question_id === questionId);
    
    if (existingIndex >= 0) {
      newAnswers[existingIndex] = { ...newAnswers[existingIndex], ...update };
    } else {
      newAnswers.push({
        question_id: questionId,
        selected_option_id: undefined,
        custom_answer: undefined,
        edited_options: [],
        ...update
      });
    }
    
    setAnswers(newAnswers);
    onAnswersChange(newAnswers);
  };

  const handleOptionSelect = (questionId: string, optionId: string) => {
    updateAnswer(questionId, {
      selected_option_id: optionId,
      custom_answer: undefined
    });
  };

  const handleCustomAnswer = (questionId: string, customAnswer: string) => {
    updateAnswer(questionId, {
      selected_option_id: undefined,
      custom_answer: customAnswer
    });
  };

  const startEditingOptions = (question: MultipleChoiceQuestion) => {
    setEditingOptions(prev => ({ ...prev, [question.id]: true }));
    setTempOptions(prev => ({ ...prev, [question.id]: [...question.options] }));
  };

  const saveEditedOptions = (questionId: string) => {
    const editedOptions = tempOptions[questionId] || [];
    updateAnswer(questionId, { edited_options: editedOptions });
    setEditingOptions(prev => ({ ...prev, [questionId]: false }));
  };

  const cancelEditingOptions = (questionId: string) => {
    setEditingOptions(prev => ({ ...prev, [questionId]: false }));
    setTempOptions(prev => {
      const newTemp = { ...prev };
      delete newTemp[questionId];
      return newTemp;
    });
  };

  const updateTempOption = (questionId: string, optionIndex: number, newText: string) => {
    setTempOptions(prev => ({
      ...prev,
      [questionId]: prev[questionId]?.map((opt, idx) => 
        idx === optionIndex ? { ...opt, text: newText } : opt
      ) || []
    }));
  };

  const getAnswerForQuestion = (questionId: string): UserAnswer | undefined => {
    return answers.find(a => a.question_id === questionId);
  };

  const getOptionsForQuestion = (question: MultipleChoiceQuestion): MultipleChoiceOption[] => {
    const answer = getAnswerForQuestion(question.id);
    if (answer?.edited_options && answer.edited_options.length > 0) {
      return answer.edited_options;
    }
    return question.options;
  };

  const isComplete = questions.length > 0 && answers.length === questions.length &&
    answers.every(a => a.selected_option_id || a.custom_answer);

  return (
    <div className="space-y-6">
      {questions.map((question, questionIndex) => {
        const answer = getAnswerForQuestion(question.id);
        const options = getOptionsForQuestion(question);
        const isEditingThisQuestion = editingOptions[question.id];

        return (
          <Card key={question.id} className="border-l-4 border-l-blue-500">
            <CardHeader>
              <CardTitle className="text-lg font-medium">
                {questionIndex + 1}. {question.question}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Answer Options */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-base font-medium">Choose an answer:</Label>
                  {question.allow_edit_options && !isEditingThisQuestion && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => startEditingOptions(question)}
                      className="flex items-center gap-1"
                    >
                      <Edit2 size={14} />
                      Edit Options
                    </Button>
                  )}
                  {isEditingThisQuestion && (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => cancelEditingOptions(question.id)}
                      >
                        <X size={14} />
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => saveEditedOptions(question.id)}
                      >
                        <Save size={14} />
                      </Button>
                    </div>
                  )}
                </div>

                {/* Render options */}
                {options.map((option, optionIndex) => (
                  <div key={option.id} className="flex items-center space-x-3">
                    {!isEditingThisQuestion ? (
                      <>
                        <input
                          type="radio"
                          id={`${question.id}-${option.id}`}
                          name={`question-${question.id}`}
                          checked={answer?.selected_option_id === option.id}
                          onChange={() => handleOptionSelect(question.id, option.id)}
                          className="h-4 w-4 text-blue-600"
                        />
                        <Label
                          htmlFor={`${question.id}-${option.id}`}
                          className="flex-1 cursor-pointer"
                        >
                          {option.text}
                        </Label>
                      </>
                    ) : (
                      <div className="flex-1 flex items-center space-x-2">
                        <span className="text-sm text-gray-500">•</span>
                        <Input
                          value={tempOptions[question.id]?.[optionIndex]?.text || ""}
                          onChange={(e) => updateTempOption(question.id, optionIndex, e.target.value)}
                          className="flex-1"
                        />
                      </div>
                    )}
                  </div>
                ))}

                {/* Other option */}
                {question.allow_other && !isEditingThisQuestion && (
                  <div className="space-y-2">
                    <div className="flex items-center space-x-3">
                      <input
                        type="radio"
                        id={`${question.id}-other`}
                        name={`question-${question.id}`}
                        checked={!!answer?.custom_answer}
                        onChange={() => handleCustomAnswer(question.id, answer?.custom_answer || "")}
                        className="h-4 w-4 text-blue-600"
                      />
                      <Label
                        htmlFor={`${question.id}-other`}
                        className="cursor-pointer font-medium"
                      >
                        Other (please specify):
                      </Label>
                    </div>
                    {(answer?.custom_answer !== undefined) && (
                      <Textarea
                        value={answer.custom_answer || ""}
                        onChange={(e) => handleCustomAnswer(question.id, e.target.value)}
                        placeholder="Please provide your own answer..."
                        className="mt-2"
                        rows={3}
                      />
                    )}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        );
      })}

      {/* Submit Button */}
      {questions.length > 0 && (
        <div className="flex justify-end pt-4">
          <Button
            onClick={onSubmit}
            disabled={!isComplete || isLoading}
            size="lg"
            className="px-8"
          >
            {isLoading ? "Processing..." : "Submit Answers"}
          </Button>
        </div>
      )}
    </div>
  );
} 