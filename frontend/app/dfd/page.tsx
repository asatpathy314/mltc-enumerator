"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

const dfdSchema = z.object({
  textual_dfd: z.string().min(10, "DFD description must be at least 10 characters"),
});

type DfdFormValues = z.infer<typeof dfdSchema>;

export default function DfdPage() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<DfdFormValues>({
    resolver: zodResolver(dfdSchema),
    defaultValues: { textual_dfd: "" },
  });

  const onSubmit = (values: DfdFormValues) => {
    setIsSubmitting(true);
    try {
      const payload = {
        textual_dfd: values.textual_dfd,
        questions: [],
        answers: [],
      };
      const searchParams = new URLSearchParams();
      searchParams.append("data", JSON.stringify(payload));
      window.location.href = `/dfd/processing?${searchParams.toString()}`;
    } catch (err) {
      toast.error("Failed to submit DFD");
      console.error(err);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Data-Flow Diagram Refinement</h1>
      <Card>
        <CardHeader>
          <CardTitle>Initial DFD Description</CardTitle>
          <CardDescription>
            Provide your raw textual description of the system&apos;s data-flow diagram. The LLM will ask follow-up questions to refine it.
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
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Submitting…" : "Next"}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
} 