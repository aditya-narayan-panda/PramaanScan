import { useState, type FormEvent } from "react";
import { Mail, MessageSquareText, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";

const SUPPORT_EMAIL = "support@pramaanscan.example";

export default function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  const handleSend = (e: FormEvent) => {
    e.preventDefault();
    const subject = encodeURIComponent(`PramaanScan inquiry from ${name || "website visitor"}`);
    const body = encodeURIComponent(`${message}\n\n— ${name} (${email})`);
    window.location.href = `mailto:${SUPPORT_EMAIL}?subject=${subject}&body=${body}`;
  };

  return (
    <div className="container max-w-4xl py-16 sm:py-20">
      <div className="text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <MessageSquareText className="h-6 w-6" />
        </div>
        <h1 className="mt-5 font-display text-3xl font-bold sm:text-4xl">Get in touch</h1>
        <p className="mt-3 text-muted-foreground">
          Questions about verification, or want to onboard your institution? Reach out.
        </p>
      </div>

      <div className="mt-12 grid gap-8 lg:grid-cols-[1fr_1.3fr]">
        <Card className="h-fit">
          <CardContent className="p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Mail className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-semibold">Email</p>
                <a href={`mailto:${SUPPORT_EMAIL}`} className="text-sm text-primary hover:underline">
                  {SUPPORT_EMAIL}
                </a>
              </div>
            </div>
            <p className="mt-5 text-xs leading-relaxed text-muted-foreground">
              Submitting the form opens your email client with the message pre-filled — PramaanScan
              doesn't run a contact-form backend, so nothing is silently sent or stored on our
              servers.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <form onSubmit={handleSend} className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="name">Your name</Label>
                  <Input id="name" required value={name} onChange={(e) => setName(e.target.value)} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="email">Your email</Label>
                  <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="message">Message</Label>
                <Textarea
                  id="message"
                  required
                  rows={6}
                  className="font-sans"
                  placeholder="How can we help?"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full sm:w-auto">
                <Send className="h-4 w-4" />
                Open in email client
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
