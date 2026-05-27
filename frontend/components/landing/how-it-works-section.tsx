"use client"

import { Upload, Sparkles, LayoutDashboard } from "lucide-react"

const steps = [
  {
    number: 1,
    icon: Upload,
    title: "Tải ảnh hóa đơn",
    description: "Kéo thả hoặc chọn file ảnh hóa đơn từ thiết bị của bạn",
  },
  {
    number: 2,
    icon: Sparkles,
    title: "AI xử lý tự động",
    description: "Gemini Vision trích xuất thông tin: ngày, nhà cung cấp, sản phẩm, tổng tiền",
  },
  {
    number: 3,
    icon: LayoutDashboard,
    title: "Xem kết quả & quản lý",
    description: "Duyệt hóa đơn, phân loại danh mục và xem báo cáo chi tiết",
  },
]

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
            Cách hoạt động
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
            Chỉ 3 bước đơn giản để bắt đầu quản lý hóa đơn
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
          {steps.map((step, index) => (
            <div
              key={step.number}
              className="relative text-center animate-in fade-in slide-in-from-bottom-4 duration-700"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-10 left-[60%] w-[80%] h-[2px] bg-gradient-to-r from-primary/30 to-primary/10" />
              )}

              {/* Step number */}
              <div className="relative inline-flex items-center justify-center w-20 h-20 mb-6">
                <div className="absolute inset-0 bg-primary/10 rounded-full" />
                <div className="relative w-14 h-14 bg-primary rounded-full flex items-center justify-center shadow-lg">
                  <span className="text-xl font-bold text-primary-foreground">{step.number}</span>
                </div>
              </div>

              {/* Icon */}
              <div className="w-12 h-12 mx-auto mb-4 bg-secondary rounded-xl flex items-center justify-center">
                <step.icon className="w-6 h-6 text-primary" />
              </div>

              {/* Content */}
              <h3 className="text-xl font-semibold text-foreground mb-2">
                {step.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed max-w-xs mx-auto">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
