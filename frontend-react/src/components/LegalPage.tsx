import Nav from "@/components/Nav"
import Footer from "@/components/Footer"

function LegalPage({ title }: { title: string }) {
  return (
    <div className="min-h-screen bg-paper flex flex-col">
      <Nav />
      <div className="flex-1 px-6 md:px-10 py-20 max-w-3xl mx-auto w-full">
        <h1 className="font-display text-3xl text-ink">{title}</h1>
        <p className="mt-4 text-muted-foreground">
          This page is a placeholder — content coming soon.
        </p>
      </div>
      <Footer />
    </div>
  )
}

export default LegalPage