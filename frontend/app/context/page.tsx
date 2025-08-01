"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { EnumerateRequest } from "@/lib/api";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const contextFormSchema = z.object({
  textual_dfd: z.string().min(10, "DFD description must be at least 10 characters"),
  extra_prompt: z.string().optional(),
  questions: z.array(z.string()),
  answers: z.array(z.string()),
});

type ContextFormValues = z.infer<typeof contextFormSchema>;

export default function ContextPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Initialize with two empty Q&A fields
  const [defaultValues, setDefaultValues] = useState<Partial<ContextFormValues>>({
    textual_dfd: "",
    extra_prompt: "",
    questions: ["", ""],
    answers: ["", ""],
  });

  useEffect(() => {
    const prefillDfd = sessionStorage.getItem("contextPrefillDfd");
    const prefillQuestions = sessionStorage.getItem("contextPrefillQuestions");
    const prefillAnswers = sessionStorage.getItem("contextPrefillAnswers");
    
    const updates: Partial<ContextFormValues> = {};
    
    if (prefillDfd) {
      updates.textual_dfd = prefillDfd;
    }
    
    if (prefillQuestions && prefillAnswers) {
      try {
        const questions = JSON.parse(prefillQuestions);
        const answers = JSON.parse(prefillAnswers);
        if (Array.isArray(questions) && Array.isArray(answers)) {
          updates.questions = questions;
          updates.answers = answers;
        }
      } catch (error) {
        console.error("Failed to parse prefilled Q&A:", error);
      }
    }
    
    if (Object.keys(updates).length > 0) {
      setDefaultValues((prev) => ({ ...prev, ...updates }));
    }
  }, []);

  const form = useForm<ContextFormValues>({
    resolver: zodResolver(contextFormSchema),
    defaultValues,
  });

  // reset when prefill updated
  useEffect(() => {
    form.reset(defaultValues as ContextFormValues);
  }, [defaultValues, form]);

  const onSubmit = async (values: ContextFormValues) => {
    setIsSubmitting(true);
    try {
      // Filter out empty questions and answers
      const filteredQuestions = values.questions.filter(q => q.trim() !== '');
      const filteredAnswers = values.answers.filter(a => a.trim() !== '');
      
      // Create request payload (empty context for initial enumeration)
      const request: EnumerateRequest = {
        textual_dfd: values.textual_dfd,
        extra_prompt: values.extra_prompt,
        attackers: [],
        entry_points: [],
        assets: [],
        assumptions: [],
        questions: filteredQuestions,
        answers: filteredAnswers,
      };
      
      // Store request data in sessionStorage instead of URL
      sessionStorage.setItem("contextRequest", JSON.stringify(request));
      
      // Redirect to loading page without data in URL
      window.location.href = `/context/processing`;
    } catch (error) {
      toast.error("Failed to submit form");
      console.error(error);
      setIsSubmitting(false);
    }
  };

  const addQuestionField = () => {
    const currentQuestions = form.getValues("questions");
    const currentAnswers = form.getValues("answers");
    form.setValue("questions", [...currentQuestions, ""]);
    form.setValue("answers", [...currentAnswers, ""]);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Context Enumeration</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Data Flow Diagram Description</CardTitle>
          <CardDescription>
            Provide a detailed description of your system&apos;s data flow diagram
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
              <FormField
                control={form.control}
                name="textual_dfd"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Data Flow Diagram Description</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Describe your system&apos;s data flow diagram..."
                        className="min-h-[200px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Include details about components, data flows, and trust boundaries
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="extra_prompt"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Additional Context (Optional)</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Add any additional context or hints..."
                        className="min-h-[100px]"
                        {...field}
                      />
                    </FormControl>
                    <FormDescription>
                      Provide any extra information that might help with the analysis
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium">Contextual Questions & Answers</h3>
                  <Button type="button" variant="outline" onClick={addQuestionField}>
                    Add Question
                  </Button>
                </div>
                
                {form.getValues("questions").map((_, index) => (
                  <div key={index} className="grid gap-4 mb-6">
                    <FormField
                      control={form.control}
                      name={`questions.${index}`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>{`Question ${index + 1}`}</FormLabel>
                          <FormControl>
                            <Input placeholder="Enter question..." {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    
                    <FormField
                      control={form.control}
                      name={`answers.${index}`}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>{`Answer ${index + 1}`}</FormLabel>
                          <FormControl>
                            <Textarea placeholder="Enter answer..." {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                ))}
              </div>
              
              <div className="flex justify-end">
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Processing..." : "Generate Context"}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
} 