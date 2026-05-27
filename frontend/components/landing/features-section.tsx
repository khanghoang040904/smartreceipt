"use client"

import { Camera, MessageSquare, CheckCircle, Upload, BarChart3, Receipt } from "lucide-react"

const features = [
  {
    icon: Camera,
    title: "OCR thông minh",
    description: "Chụp ảnh hóa đơn, AI trích xuất nhà cung cấp, sản phẩm, tổng tiền tự động",
  },
  {
    icon: MessageSquare,
    title: "Trợ lý AI",
    description: "Hỏi đáp tự nhiên về chi tiêu: \"Tháng này mình chi bao nhiêu cho thực phẩm?\"",
  },
  {
    icon: CheckCircle,
    title: "Duyệt hóa đơn",
    description: "Quy trình duyệt hóa đơn: Chờ duyệt → Đã duyệt / Từ chối",
  },
  {
    icon: Upload,
    title: "Tải hàng loạt",
    description: "Upload nhiều hóa đơn cùng lúc, xử lý batch tự động",
  },
  {
    icon: BarChart3,
    title: "Báo cáo chi tiết",
    description: "Biểu đồ chi tiêu theo danh mục, theo tháng, top nhà cung cấp, xuất CSV",
  },
  {
    icon: Receipt,
    title: "VAT & Giảm giá",
    description: "Tự động trích xuất thuế VAT, giảm giá, so khớp tổng tiền",
  },
]

export function FeaturesSection() {
  return (
    <section id="features" className="py-20 bg-secondary/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
            Tính năng nổi bật
          </h2>
          <p className="mt-4 text-lg text-muted-foreground max-w-2xl mx-auto">
            Tất cả những gì bạn cần để quản lý hóa đơn hiệu quả
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={feature.title}
              className="group bg-card rounded-xl border border-border shadow-sm p-6 hover:shadow-md transition-all duration-300 hover:-translate-y-1 animate-in fade-in slide-in-from-bottom-4"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
