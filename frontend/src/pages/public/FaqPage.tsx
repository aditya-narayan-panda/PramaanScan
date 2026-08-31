import { motion } from "framer-motion";
import { HelpCircle } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { FAQ_ITEMS } from "@/lib/faqData";

export default function FaqPage() {
  return (
    <div className="container max-w-3xl py-16 sm:py-20">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <HelpCircle className="h-6 w-6" />
        </div>
        <h1 className="mt-5 font-display text-3xl font-bold sm:text-4xl">Frequently Asked Questions</h1>
        <p className="mt-3 text-muted-foreground">
          Everything you need to know about how PramaanScan verifies official communications.
        </p>
      </motion.div>

      <div className="mt-12">
        <Accordion type="single" collapsible className="space-y-3">
          {FAQ_ITEMS.map((item) => (
            <AccordionItem key={item.question} value={item.question}>
              <AccordionTrigger>{item.question}</AccordionTrigger>
              <AccordionContent>{item.answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}
