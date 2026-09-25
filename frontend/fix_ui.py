import os

path = "src/app/page.tsx"
with open(path, "r") as f:
    content = f.read()

replacements = {
    # Layout & Base
    'bg-[#F8FAFC]': 'bg-[#06040A]', # Extremely dark royal background
    'bg-white': 'bg-white/5 backdrop-blur-xl',
    'bg-gray-50': 'bg-white/[0.02]',
    'bg-gray-100': 'bg-white/5',
    'bg-gray-200': 'bg-white/10',
    
    # Borders
    'border-gray-100': 'border-white/5',
    'border-gray-200': 'border-white/10',
    'border-gray-300': 'border-white/20',
    
    # Text
    'text-gray-900': 'text-white font-light tracking-wide',
    'text-gray-800': 'text-white/90',
    'text-gray-700': 'text-white/80',
    'text-gray-600': 'text-white/70',
    'text-gray-500': 'text-white/50',
    'text-gray-400': 'text-white/40',
    
    # Royal Accents (Blue -> Gold/Amber)
    'bg-blue-50': 'bg-amber-500/10 border-l-2 border-amber-500',
    'text-blue-700': 'text-amber-400 font-medium',
    'text-blue-600': 'text-amber-400',
    'text-blue-500': 'text-amber-500',
    'border-blue-200': 'border-amber-500/20',
    'border-blue-500': 'border-amber-500/50',
    
    # Primary Buttons
    'bg-blue-600': 'bg-gradient-to-r from-amber-600 via-yellow-500 to-amber-600 border border-amber-400/30 shadow-[0_0_15px_rgba(245,158,11,0.3)]',
    'hover:bg-blue-700': 'hover:shadow-[0_0_25px_rgba(245,158,11,0.5)] hover:border-amber-300/50 transition-all duration-300',
    
    # Secondary accents (Green -> Emerald/Jewel)
    'bg-green-50': 'bg-emerald-500/10 border border-emerald-500/20',
    'text-green-700': 'text-emerald-400',
    'text-green-600': 'text-emerald-400',
    'bg-green-500': 'bg-gradient-to-r from-emerald-500 to-teal-400 shadow-[0_0_15px_rgba(16,185,129,0.3)]',
    
    # Progress bar and decorative
    'from-blue-600 to-indigo-600': 'from-amber-500 via-yellow-400 to-amber-500 bg-[length:200%_auto] animate-[gradient_2s_linear_infinite]',
    'shadow-sm': 'shadow-[0_4px_20px_-2px_rgba(0,0,0,0.5)]',
    'shadow-md': 'shadow-[0_8px_30px_-4px_rgba(0,0,0,0.6)]',
    
    # Fix nested glass
    'bg-white rounded-lg shadow-sm': 'bg-white/[0.03] rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.4)] border border-white/10 backdrop-blur-2xl ring-1 ring-white/5',
    'bg-white rounded-xl shadow-sm': 'bg-white/[0.03] rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.4)] border border-white/10 backdrop-blur-2xl ring-1 ring-white/5',
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Add some global background glows
content = content.replace(
    '<div className="flex h-screen bg-[#06040A] text-white font-light tracking-wide font-sans overflow-hidden">',
    '''<div className="flex h-screen bg-[#06040A] text-white font-light tracking-wide font-sans overflow-hidden relative">
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-0">
        <div className="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-900/20 blur-[150px]"></div>
        <div className="absolute bottom-[20%] -right-[10%] w-[40%] h-[40%] rounded-full bg-amber-900/10 blur-[150px]"></div>
      </div>
      <div className="flex w-full h-full relative z-10">'''
)

content = content.replace(
    '</div>\n    </div>\n  );\n}',
    '</div>\n      </div>\n    </div>\n  );\n}'
)

with open(path, "w") as f:
    f.write(content)
print("Done styling page.tsx")
