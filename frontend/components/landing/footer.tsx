import Link from "next/link"
import { Receipt } from "lucide-react"

export function Footer() {
  return (
    <footer className="py-12 border-t border-border bg-secondary/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
              <Receipt className="w-4 h-4 text-primary-foreground" />
            </div>
            <span className="font-bold text-foreground">SmartReceipt</span>
          </Link>

          {/* Links */}
          <nav className="flex items-center gap-6 text-sm">
            <Link href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
              Tính năng
            </Link>
            <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
              Hỗ trợ
            </Link>
            <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
              Điều khoản
            </Link>
          </nav>

          {/* Copyright */}
          <p className="text-sm text-muted-foreground">
            © 2025 SmartReceipt
          </p>
        </div>
      </div>
    </footer>
  )
}
