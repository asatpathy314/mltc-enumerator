import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { 
  ThreatVerificationQuestion, 
  ThreatVerificationAnswer,
  ThreatChain,
  ContextEnumeration
} from "@/lib/api";
import { 
  CheckCircle, 
  AlertTriangle, 
  HelpCircle, 
  Shield, 
  Target,
  ChevronRight,
  ChevronLeft
} from "lucide-react";

interface ThreatVerificationProps {
  questions: ThreatVerificationQuestion[];
  threatChains: ThreatChain[];
  context: ContextEnumeration;
  onComplete: (answers: ThreatVerificationAnswer[]) => void;
  onCancel: () => void;
}

export default function ThreatVerification({
  questions,
  onComplete,
  onCancel
}: ThreatVerificationProps) {
  const [answers, setAnswers] = useState<ThreatVerificationAnswer[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showSummary, setShowSummary] = useState(false);

  // Group questions by threat
  const questionsByThreat = questions.reduce((acc, question) => {
    if (!acc[question.threat_name]) {
      acc[question.threat_name] = [];
    }
    acc[question.threat_name].push(question);
    return acc;
  }, {} as Record<string, ThreatVerificationQuestion[]>);

  const threatNames = Object.keys(questionsByThreat);
  const totalQuestions = questions.length;
  const answeredQuestions = answers.length;
  const progress = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;

  const handleAnswerChange = (
    questionId: string,
    threatName: string,
    selectedOptionId?: string,
    customAnswer?: string,
    confidenceLevel: number = 3
  ) => {
    const existingAnswerIndex = answers.findIndex(a => a.question_id === questionId);
    const newAnswer: ThreatVerificationAnswer = {
      question_id: questionId,
      threat_name: threatName,
      selected_option_id: selectedOptionId,
      custom_answer: customAnswer,
      confidence_level: confidenceLevel
    };

    if (existingAnswerIndex >= 0) {
      const updatedAnswers = [...answers];
      updatedAnswers[existingAnswerIndex] = newAnswer;
      setAnswers(updatedAnswers);
    } else {
      setAnswers([...answers, newAnswer]);
    }
  };

  const getAnswerForQuestion = (questionId: string): ThreatVerificationAnswer | undefined => {
    return answers.find(a => a.question_id === questionId);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'feasibility': return <Target className="w-4 h-4" />;
      case 'context': return <HelpCircle className="w-4 h-4" />;
      case 'prerequisites': return <Shield className="w-4 h-4" />;
      case 'impact': return <AlertTriangle className="w-4 h-4" />;
      default: return <CheckCircle className="w-4 h-4" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'feasibility': return 'bg-blue-100 text-blue-800';
      case 'context': return 'bg-green-100 text-green-800';
      case 'prerequisites': return 'bg-orange-100 text-orange-800';
      case 'impact': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      setShowSummary(true);
    }
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const handleComplete = () => {
    onComplete(answers);
  };

  if (questions.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>No Verification Questions</CardTitle>
          <CardDescription>
            No verification questions were generated for the threats.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button onClick={onCancel} variant="outline">
              Back to Threats
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (showSummary) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Verification Summary</CardTitle>
            <CardDescription>
              Review your answers before filtering the threats
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                <div>
                  <p className="font-medium">Progress Complete</p>
                  <p className="text-sm text-muted-foreground">
                    Answered {answeredQuestions} of {totalQuestions} questions
                  </p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>

              {threatNames.map(threatName => {
                const threatQuestions = questionsByThreat[threatName];
                const threatAnswers = answers.filter(a => a.threat_name === threatName);
                
                return (
                  <Card key={threatName} className="border-l-4 border-l-blue-500">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg">{threatName}</CardTitle>
                      <CardDescription>
                        {threatAnswers.length} of {threatQuestions.length} questions answered
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {threatAnswers.map(answer => {
                          const question = questions.find(q => q.id === answer.question_id);
                          return (
                            <div key={answer.question_id} className="text-sm">
                              <p className="font-medium">{question?.question}</p>
                              <p className="text-muted-foreground">
                                {answer.custom_answer || answer.selected_option_id}
                                <span className="ml-2 text-xs">
                                  (Confidence: {answer.confidence_level}/5)
                                </span>
                              </p>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}

              <div className="flex gap-4 pt-4">
                <Button onClick={() => setShowSummary(false)} variant="outline">
                  <ChevronLeft className="w-4 h-4 mr-2" />
                  Back to Questions
                </Button>
                <Button onClick={handleComplete} className="flex-1">
                  Filter Threats Based on Answers
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const currentAnswer = getAnswerForQuestion(currentQuestion.id);

  return (
    <div className="space-y-6">
      {/* Progress Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Threat Verification</CardTitle>
              <CardDescription>
                Answer questions to verify threat plausibility in your context
              </CardDescription>
            </div>
            <Badge variant="outline">
              {currentQuestionIndex + 1} of {totalQuestions}
            </Badge>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Progress</span>
              <span>{Math.round(progress)}% complete</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>
        </CardHeader>
      </Card>

      {/* Current Question */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <Badge className={getCategoryColor(currentQuestion.category)}>
              {getCategoryIcon(currentQuestion.category)}
              <span className="ml-1 capitalize">{currentQuestion.category}</span>
            </Badge>
            <div className="text-sm text-muted-foreground">
              Threat: {currentQuestion.threat_name}
            </div>
          </div>
          <CardTitle className="text-xl">{currentQuestion.question}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Answer Options */}
          <div className="space-y-3">
            {currentQuestion.options.map((option) => (
              <div
                key={option.id}
                className={`p-4 border rounded-lg cursor-pointer transition-all hover:bg-muted/50 ${
                  currentAnswer?.selected_option_id === option.id
                    ? 'border-primary bg-primary/5'
                    : 'border-border'
                }`}
                onClick={() => handleAnswerChange(
                  currentQuestion.id,
                  currentQuestion.threat_name,
                  option.id,
                  undefined,
                  currentAnswer?.confidence_level || 3
                )}
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-4 h-4 rounded-full border-2 ${
                      currentAnswer?.selected_option_id === option.id
                        ? 'border-primary bg-primary'
                        : 'border-muted-foreground'
                    }`}
                  />
                  <span className="flex-1">{option.text}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Custom Answer Option */}
          <div className="space-y-3">
            <Label>Or provide a custom answer:</Label>
            <Textarea
              placeholder="Describe your specific situation..."
              value={currentAnswer?.custom_answer || ''}
              onChange={(e) => handleAnswerChange(
                currentQuestion.id,
                currentQuestion.threat_name,
                undefined,
                e.target.value,
                currentAnswer?.confidence_level || 3
              )}
              className="min-h-[100px]"
            />
          </div>

          {/* Confidence Level */}
          {(currentAnswer?.selected_option_id || currentAnswer?.custom_answer) && (
            <div className="space-y-3">
              <Label>Confidence Level</Label>
              <Select
                value={currentAnswer.confidence_level.toString()}
                onValueChange={(value) => handleAnswerChange(
                  currentQuestion.id,
                  currentQuestion.threat_name,
                  currentAnswer.selected_option_id,
                  currentAnswer.custom_answer,
                  parseInt(value)
                )}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select confidence level" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 - Very Low Confidence</SelectItem>
                  <SelectItem value="2">2 - Low Confidence</SelectItem>
                  <SelectItem value="3">3 - Medium Confidence</SelectItem>
                  <SelectItem value="4">4 - High Confidence</SelectItem>
                  <SelectItem value="5">5 - Very High Confidence</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between pt-4">
            <Button
              onClick={handlePrevious}
              variant="outline"
              disabled={currentQuestionIndex === 0}
            >
              <ChevronLeft className="w-4 h-4 mr-2" />
              Previous
            </Button>

            <div className="flex gap-2">
              <Button onClick={onCancel} variant="outline">
                Cancel
              </Button>
              
              {currentQuestionIndex === questions.length - 1 ? (
                <Button onClick={() => setShowSummary(true)}>
                  Review Answers
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <Button onClick={handleNext}>
                  Next
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          <strong>Why verify threats?</strong> This process helps identify which threats are realistic
          in your specific environment, removing false positives and focusing on actionable security concerns.
        </AlertDescription>
      </Alert>
    </div>
  );
} 