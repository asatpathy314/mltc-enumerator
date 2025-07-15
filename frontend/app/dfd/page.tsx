"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";
import DfdChat from "@/components/dfd-chat";

const dfdSchema = z.object({
  textual_dfd: z.string().min(10, "DFD description must be at least 10 characters"),
});

type DfdFormValues = z.infer<typeof dfdSchema>;

export default function DfdPage() {
  const router = useRouter();
  const [showChat, setShowChat] = useState(false);
  const [initialDfd, setInitialDfd] = useState("");

  const form = useForm<DfdFormValues>({
    resolver: zodResolver(dfdSchema),
    defaultValues: { textual_dfd: "" },
  });

  const onSubmit = (values: DfdFormValues) => {
    setInitialDfd(values.textual_dfd);
    setShowChat(true);
  };

  const handleChatComplete = (dfd: string, questions: string[], answers: string[]) => {
    // Store DFD and Q&A for context enumeration
    sessionStorage.setItem("contextPrefillDfd", dfd);
    sessionStorage.setItem("contextPrefillQuestions", JSON.stringify(questions));
    sessionStorage.setItem("contextPrefillAnswers", JSON.stringify(answers));
    toast.success("DFD Q&A collection complete!");
    router.push("/context");
  };

  if (showChat) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-3">ML Security Assessment</h1>
          <p className="text-gray-600 text-lg">
            The assistant will ask questions to better understand your ML system&apos;s security context. Answer them to provide additional context for threat enumeration.
          </p>
        </div>
        <DfdChat initialDfd={initialDfd} onComplete={handleChatComplete} />
        <div className="mt-6 flex justify-start">
          <Button variant="outline" onClick={() => setShowChat(false)}>
            Back to DFD Entry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Data-Flow Diagram Refinement</h1>
      <Card>
        <CardHeader>
          <CardTitle>Initial DFD Description</CardTitle>
          <CardDescription>
            Provide your raw textual description of the system&apos;s data-flow diagram. The assistant will ask follow-up questions to refine it.
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
                    <FormLabel>Data-Flow Diagram</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Describe the components, data flows, trust boundaries …"
                        className="min-h-[200px]"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex justify-end">
                <Button type="submit">Start Refinement Chat</Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
} 