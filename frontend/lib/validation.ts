import { z } from "zod";

export const eventCreateSchema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Event name must be at least 2 characters.")
    .max(200, "Event name must be under 200 characters."),
  event_type: z.enum(["birthday", "wedding", "community"]),
  location: z
    .string()
    .trim()
    .min(2, "Location is required (e.g., Chennai, Bengaluru).")
    .max(200, "Location must be under 200 characters."),
  total_budget: z.coerce
    .number()
    .int("Budget must be a whole integer in INR.")
    .min(1000, "Total budget must be at least ₹1,000 INR.")
    .max(1000000000, "Total budget exceeds maximum limit."),
  guest_count: z.coerce
    .number()
    .int("Guest count must be a whole number.")
    .min(1, "Guest count must be at least 1.")
    .max(100000, "Guest count cannot exceed 100,000."),
  event_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Event date must be in YYYY-MM-DD format."),
  preferred_theme: z.string().max(200).optional().default(""),
  dietary_requirements: z.string().max(300).optional().default(""),
  additional_preferences: z.string().max(2000).optional().default(""),
});

export type EventCreateFormValues = z.infer<typeof eventCreateSchema>;

export const expenseCreateSchema = z.object({
  category_name: z.string().trim().min(2, "Select a category."),
  title: z.string().trim().min(2, "Enter an expense title.").max(200),
  amount: z.coerce
    .number()
    .int("Amount must be an integer in INR.")
    .min(1, "Expense amount must be at least ₹1 INR."),
  incurred_date: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Date must be YYYY-MM-DD."),
  notes: z.string().max(500).optional().default(""),
});

export type ExpenseCreateFormValues = z.infer<typeof expenseCreateSchema>;

export const knowledgeEntrySchema = z.object({
  title: z.string().trim().min(3, "Title must be at least 3 characters.").max(250),
  content: z
    .string()
    .trim()
    .min(20, "Knowledge content must be at least 20 characters.")
    .max(100000),
  event_type: z.enum(["wedding", "birthday", "community", "general"]),
  category: z.string().trim().min(2, "Category is required.").max(100),
  location: z.string().trim().min(2, "Location is required.").max(150),
  source_label: z.string().trim().min(2, "Source label is required.").max(250),
  is_illustrative: z.boolean().default(true),
});

export type KnowledgeEntryFormValues = z.infer<typeof knowledgeEntrySchema>;
