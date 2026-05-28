"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Building2,
  ClipboardCheck,
  Footprints,
  FileText,
  Rocket,
  Sparkles,
} from "lucide-react";

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  action: string;
  actionLabel: string;
  href: string;
  completed: boolean;
}

interface OnboardingWizardProps {
  isNewUser?: boolean;
  onComplete?: () => void;
}

export function OnboardingWizard({
  isNewUser = false,
  onComplete,
}: OnboardingWizardProps) {
  const router = useRouter();
  const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [isOpen, setIsOpen] = useState(isNewUser);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());

  const steps: OnboardingStep[] = [
    {
      id: "company",
      title: "Profilo Azienda",
      description:
        "Configura i dati della tua azienda: settore, paese, numero dipendenti. Questi dati sono essenziali per la valutazione CSRD.",
      icon: <Building2 className="w-8 h-8 text-blue-600" />,
      action: "Vai al profilo azienda",
      actionLabel: "Configura",
      href: "/settings",
      completed: false,
    },
    {
      id: "assessment",
      title: "Questionario di Contesto",
      description:
        "Rispondi al questionario di contesto aziendale. Ci aiuta a personalizzare la valutazione di doppia materialità per il tuo settore.",
      icon: <ClipboardCheck className="w-8 h-8 text-green-600" />,
      action: "Avvia questionario",
      actionLabel: "Inizia",
      href: "/assessment",
      completed: false,
    },
    {
      id: "emissions",
      title: "Calcolo Emissioni GHG",
      description:
        "Inserisci i dati per calcolare le emissioni Scope 1, 2 e 3 secondo il GHG Protocol. Fondamentale per il report CSRD.",
      icon: <Footprints className="w-8 h-8 text-orange-600" />,
      action: "Calcola emissioni",
      actionLabel: "Calcola",
      href: "/emissions",
      completed: false,
    },
    {
      id: "report",
      title: "Genera il Report CSRD",
      description:
        "Una volta completati i passi precedenti, genera il report CSRD completo con tagging iXBRL e validazione automatica.",
      icon: <FileText className="w-8 h-8 text-purple-600" />,
      action: "Genera report",
      actionLabel: "Genera",
      href: "/reports",
      completed: false,
    },
    {
      id: "complete",
      title: "Sei Pronto! 🚀",
      description:
        "Hai completato la configurazione iniziale. Ora puoi esplorare la dashboard, monitorare la conformità e gestire i tuoi report.",
      icon: <Rocket className="w-8 h-8 text-indigo-600" />,
      action: "Vai alla dashboard",
      actionLabel: "Inizia",
      href: "/dashboard",
      completed: false,
    },
  ];

  // Check which steps are already completed
  useEffect(() => {
    const checkCompleted = async () => {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) return;

        const completed = new Set<string>();

        // Check company profile
        const companyRes = await fetch("/api/v1/companies/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (companyRes.ok) {
          const company = await companyRes.json();
          if (company.company_name && company.sector !== "Unknown") {
            completed.add("company");
          }
        }

        // Check assessment
        const assessmentRes = await fetch("/api/v1/assessment/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (assessmentRes.ok) {
          const assessments = await assessmentRes.json();
          if (Array.isArray(assessments) && assessments.length > 0) {
            completed.add("assessment");
          }
        }

        // Check emissions
        const emissionsRes = await fetch("/api/v1/emissions/summary", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (emissionsRes.ok) {
          const emissions = await emissionsRes.json();
          if (emissions.total_emissions && emissions.total_emissions > 0) {
            completed.add("emissions");
          }
        }

        // Check reports
        const reportsRes = await fetch("/api/v1/reports/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (reportsRes.ok) {
          const reports = await reportsRes.json();
          if (Array.isArray(reports) && reports.length > 0) {
            completed.add("report");
          }
        }

        setCompletedSteps(completed);
      } catch (err) {
        // Silently fail — user may not be authenticated yet
      }
    };

    if (isOpen) {
      checkCompleted();
    }
  }, [isOpen]);

  const totalSteps = steps.length;
  const progress = Math.round(
    ((currentStep + 1) / totalSteps) * 100
  );

  const handleNext = () => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleAction = () => {
    const step = steps[currentStep];
    if (step.id === "complete") {
      setIsOpen(false);
      if (onComplete) onComplete();
      // Mark onboarding as completed
      localStorage.setItem("onboarding_completed", "true");
    }
    router.push(step.href);
  };

  const handleSkip = () => {
    setIsOpen(false);
    localStorage.setItem("onboarding_completed", "true");
    if (onComplete) onComplete();
  };

  if (!isOpen) {
    return null;
  }

  const step = steps[currentStep];
  const isLastStep = currentStep === totalSteps - 1;
  const isFirstStep = currentStep === 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <Card className="w-full max-w-2xl mx-4 bg-white shadow-2xl rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="w-6 h-6 text-yellow-300" />
              <h2 className="text-xl font-bold text-white">
                Benvenuto in CSRD Comply!
              </h2>
            </div>
            <button
              onClick={handleSkip}
              className="text-white/70 hover:text-white text-sm transition-colors"
            >
              Salta
            </button>
          </div>
          <p className="text-blue-100 mt-2 text-sm">
            Ti guideremo attraverso i passi fondamentali per iniziare.
          </p>

          {/* Progress bar */}
          <div className="mt-4">
            <div className="flex justify-between text-xs text-blue-100 mb-1">
              <span>
                Passo {currentStep + 1} di {totalSteps}
              </span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} className="h-2 bg-blue-400/30" />
          </div>
        </div>

        {/* Step indicators */}
        <div className="flex justify-center gap-2 px-8 pt-4 pb-2">
          {steps.map((s, idx) => (
            <div
              key={s.id}
              className={`flex items-center gap-1 text-xs transition-colors ${
                idx === currentStep
                  ? "text-blue-600 font-semibold"
                  : completedSteps.has(s.id)
                  ? "text-green-600"
                  : "text-gray-400"
              }`}
            >
              {completedSteps.has(s.id) ? (
                <CheckCircle2 className="w-4 h-4" />
              ) : (
                <div
                  className={`w-2 h-2 rounded-full ${
                    idx === currentStep
                      ? "bg-blue-600"
                      : "bg-gray-300"
                  }`}
                />
              )}
              <span className="hidden sm:inline">{s.title}</span>
            </div>
          ))}
        </div>

        {/* Step content */}
        <div className="px-8 py-6">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 p-3 bg-gray-50 rounded-xl">
              {step.icon}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {step.title}
              </h3>
              <p className="text-gray-600 leading-relaxed">
                {step.description}
              </p>

              {/* Completion status */}
              {completedSteps.has(step.id) && (
                <Badge
                  variant="outline"
                  className="mt-3 bg-green-50 text-green-700 border-green-200"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                  Completato
                </Badge>
              )}
            </div>
          </div>
        </div>

        {/* Navigation footer */}
        <div className="px-8 py-4 bg-gray-50 border-t flex items-center justify-between">
          <div>
            {!isFirstStep && (
              <Button variant="outline" onClick={handlePrev} size="sm">
                <ArrowLeft className="w-4 h-4 mr-1" />
                Indietro
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            {!isLastStep && (
              <Button variant="ghost" onClick={handleSkip} size="sm">
                Salta tutto
              </Button>
            )}
            <Button onClick={handleAction} size="sm">
              {step.actionLabel}
              {!isLastStep ? (
                <ArrowRight className="w-4 h-4 ml-1" />
              ) : (
                <Rocket className="w-4 h-4 ml-1" />
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

/**
 * Hook to check if onboarding should be shown.
 * Shows if user is new and hasn't completed onboarding yet.
 */
export function useOnboarding() {
  const [showOnboarding, setShowOnboarding] = useState(false);
  const { user } = useAuth();

  useEffect(() => {
    // Only show for new users who haven't completed onboarding
    const completed = localStorage.getItem("onboarding_completed");
    const isNewUser = localStorage.getItem("is_new_user");

    if (user && !completed && isNewUser === "true") {
      setShowOnboarding(true);
    }
  }, [user]);

  return {
    showOnboarding,
    setShowOnboarding,
  };
}
