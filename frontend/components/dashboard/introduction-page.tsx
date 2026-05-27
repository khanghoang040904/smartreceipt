"use client"

import { HeroSection } from "@/components/landing/hero-section"
import { FeaturesSection } from "@/components/landing/features-section"
import { HowItWorksSection } from "@/components/landing/how-it-works-section"
import { StatsSection } from "@/components/landing/stats-section"
import { CTASection } from "@/components/landing/cta-section"
import { Footer } from "@/components/landing/footer"

export function IntroductionPage() {
  return (
    <div className="-m-6">
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <StatsSection />
      <CTASection />
      <Footer />
    </div>
  )
}
