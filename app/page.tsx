import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import TickerTape from "@/components/TickerTape";
import StatsBar from "@/components/StatsBar";
import FeaturesGrid from "@/components/FeaturesGrid";
import HowItWorks from "@/components/HowItWorks";
import LiveSignalsPreview from "@/components/LiveSignalsPreview";
import TechStack from "@/components/TechStack";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />
      <HeroSection />
      <TickerTape />
      <StatsBar />
      <FeaturesGrid />
      <HowItWorks />
      <LiveSignalsPreview />
      <TechStack />
      <Footer />
    </main>
  );
}
