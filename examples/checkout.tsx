// A typical checkout form as an AI agent writes it by habit.
// Run: python plugins/rtl/skills/rtl-ui/scripts/rtl_check.py examples/
export default function Checkout() {
  return (
    <html lang="he">
      <body>
        <form className="flex flex-row-reverse space-x-4 p-6">
          <label className="text-left ml-2 tracking-wide">שם מלא</label>
          <input className="rounded-l-lg border-r-2 pl-3" type="text" />
          <input className="pl-3" type="tel" placeholder="050-000-0000" />
          <input className="pl-3" type="email" />
          <span style={{ marginRight: 8, textAlign: "left" }}>סה"כ ₪150</span>
          <div className="absolute left-1/2 -translate-x-1/2">centred, not a bug</div>
        </form>
      </body>
    </html>
  );
}
