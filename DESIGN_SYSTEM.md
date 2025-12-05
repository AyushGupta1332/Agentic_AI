# 🎨 Visual Preview & Styling Guide

## Frontend Design Overview

### Header Section
```
┌─────────────────────────────────────────────────────────────┐
│  ⚡ Agentic AI         [Connection Status]  [⚙️]  [🌙/☀️] │
│     Your intelligent assistant                               │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Gradient logo with blur effect
- Real-time connection badge (green when connected)
- Clear conversation button (trash icon)
- Dark mode toggle button

### Welcome Hero Section
```
        ╭─────────────────╮
        │  ⚡ (Gradient)  │
        │   AI Logo       │
        ╰─────────────────╯
        
  Welcome to Agentic AI
  Your intelligent assistant powered by advanced 
  AI capabilities. Ask me anything!
  
  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
  │ 🔍 Web      │  │ 📰 News     │  │ 📈 Financial│
  │ Search      │  │ Latest      │  │ Data        │
  └─────────────┘  └─────────────┘  └─────────────┘
  
  Try these questions:
  ┌──────────────────────────────────────┐
  │ ⚡ What's the latest news in tech?   │
  ├──────────────────────────────────────┤
  │ ⚡ Search for information about AI   │
  └──────────────────────────────────────┘
```

### Chat Message Area
```
                 ┌──────────────────────┐
                 │ Your Message         │
                 │ (Right-aligned)      │
                 │ Gradient Blue/Purple │
                 └──────────────────────┘
                 
 ⚡  ┌──────────────────────────────────┐
     │ AI Response                      │
     │ (Left-aligned)                   │
     │ White/Dark background           │
     │                                  │
     │ Related sources:                 │
     │ 📎 Source title (clickable)     │
     └──────────────────────────────────┘
```

### Input Area
```
┌─────────────────────────────────┐  ┌──────┐
│ Ask me anything...        0/2000│  │  →   │
│                                  │  │ Send │
└─────────────────────────────────┘  └──────┘
Powered by Agentic AI • Press Enter to send
```

---

## Color Palette

### Primary Colors
```
Indigo:   #4F46E5  🔵  (Hover: #4338CA)
Violet:   #7C3AED  🟣  (Used in gradients)
```

### Status Colors
```
Success:  #22C55E  🟢  (Connected, actions complete)
Warning:  #F59E0B  🟡  (Warnings, attention needed)
Error:    #EF4444  🔴  (Errors, disconnected)
```

### Neutral Colors
```
White:      #FFFFFF
Gray-50:    #F9FAFB  (Light background)
Gray-100:   #F3F4F6
Gray-500:   #6B7280  (Text secondary)
Gray-700:   #374151  (Text primary)
Gray-800:   #1F2937
Gray-900:   #111827  (Dark background)
```

---

## Typography

### Font Stack
**Headings & Body:**
```
'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
```

**Code:**
```
'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace
```

### Font Sizes
```
Text XS:   12px   (Secondary labels)
Text SM:   14px   (Small text, buttons)
Text Base: 16px   (Body text)
Text LG:   18px   (Larger text)
Text XL:   20px   (Section headers)
Text 2XL:  24px   (Page headers)
Text 4XL:  36px   (Hero section)
```

### Font Weights
```
300  - Light      (Secondary text)
400  - Regular    (Body text)
500  - Medium     (Labels, buttons)
600  - Semibold   (Subheadings)
700  - Bold       (Headings)
800  - Black      (Main titles)
```

---

## Spacing System

Uses 4px baseline grid:
```
0.25rem (1px)   - Extra small gaps
0.5rem  (2px)   - Small gaps
0.75rem (3px)   - Small-medium gaps
1rem    (4px)   - Standard spacing
1.5rem  (6px)   - Medium spacing
2rem    (8px)   - Large spacing
2.5rem  (10px)  - Extra large
3rem    (12px)  - Section spacing
4rem    (16px)  - Major spacing
```

---

## Border Radius

```
rounded-lg    = 0.5rem  (Messages, buttons)
rounded-xl    = 0.75rem (Cards, larger elements)
rounded-2xl   = 1rem    (Message bubbles)
rounded-3xl   = 1.5rem  (Hero icons)
rounded-full  = 9999px  (Avatar circles)
```

---

## Shadow System

```
shadow-sm    = Light shadow (cards)
shadow-md    = Medium shadow (containers)
shadow-lg    = Large shadow (floating elements)
shadow-xl    = Extra large (prominent elements)
shadow-2xl   = Massive (hero section)
```

---

## Animations & Transitions

### Standard Duration
```
75ms   - Micro interactions
100ms  - Quick transitions
150ms  - Standard transitions
200ms  - Smooth transitions
300ms  - Noticeable animations
500ms  - Longer animations
700ms  - Slow animations
1000ms - Slow, dramatic effects
```

### Custom Animations
```
@keyframes slide-in
- Fade in + slide up
- Duration: 300ms
- Used for: Messages, notifications

@keyframes fade-in
- Opacity fade
- Duration: 500ms
- Used for: Welcome screen

@keyframes pulse-glow
- Pulsing opacity
- Duration: 2s infinite
- Used for: Loading indicator

@keyframes bounce (Tailwind built-in)
- Vertical bounce
- Duration: 1s infinite
- Used for: Loading dots
```

---

## Responsive Breakpoints

```
Mobile:   < 640px      (Phone)
Tablet:   640px-1024px (iPad)
Desktop:  > 1024px     (Computer)

Tailwind prefixes:
sm:  640px   - Small devices
md:  768px   - Medium tablets
lg:  1024px  - Large tablets
xl:  1280px  - Desktops
2xl: 1536px  - Large desktops
```

---

## Component Examples

### Message Bubble (User)
```
<div class="flex justify-end">
  <div class="max-w-xl 
              bg-gradient-to-br 
              from-indigo-600 to-violet-600 
              text-white 
              rounded-2xl rounded-tr-none 
              px-5 py-3 
              shadow-lg">
    Your Message Here
  </div>
</div>
```

**Classes breakdown:**
- `flex justify-end` - Right align
- `bg-gradient-to-br` - Diagonal gradient (top-left to bottom-right)
- `from-indigo-600 to-violet-600` - Gradient colors
- `rounded-2xl` - Large border radius
- `rounded-tr-none` - Remove top-right radius
- `px-5 py-3` - Padding (20px horizontal, 12px vertical)
- `shadow-lg` - Large drop shadow

### Status Badge
```
<div class="flex items-center gap-2 
            px-3 py-2 
            bg-green-50 dark:bg-green-900/30 
            text-green-700 dark:text-green-300 
            rounded-lg 
            text-sm font-medium">
  <span class="relative flex h-2 w-2">
    <span class="animate-ping 
                 absolute inline-flex 
                 h-full w-full 
                 rounded-full 
                 bg-green-400 opacity-75"></span>
  </span>
  Connected
</div>
```

**Classes breakdown:**
- `bg-green-50 dark:bg-green-900/30` - Light background, dark in dark mode
- `animate-ping` - Pulsing animation
- `opacity-75` - 75% visible (semi-transparent)

### Input Field
```
<input class="w-full 
              px-4 py-3 pr-12 
              bg-gray-50 dark:bg-gray-700 
              border border-gray-300 dark:border-gray-600 
              rounded-xl 
              focus:outline-none focus:ring-2 focus:ring-indigo-500
              focus:border-transparent 
              dark:text-white 
              dark:placeholder-gray-400 
              transition-colors duration-200">
```

**Classes breakdown:**
- `bg-gray-50 dark:bg-gray-700` - Light/dark backgrounds
- `border border-gray-300` - Thin gray border
- `focus:ring-2 focus:ring-indigo-500` - Blue ring on focus
- `transition-colors duration-200` - Smooth color transition

### Card with Hover
```
<div class="group 
            p-6 
            bg-white dark:bg-gray-800 
            rounded-2xl 
            border border-gray-200 dark:border-gray-700 
            hover:shadow-xl 
            hover:-translate-y-1 
            transition-all duration-300 
            cursor-pointer">
  <div class="w-12 h-12 
              rounded-xl 
              group-hover:scale-110 
              transition-transform">
  </div>
</div>
```

**Classes breakdown:**
- `group` - Enables group hover states
- `hover:shadow-xl` - Larger shadow on hover
- `hover:-translate-y-1` - Move up on hover
- `group-hover:scale-110` - Scale up child on parent hover

---

## Dark Mode Implementation

### Base Setup
```html
<html class="dark">
```

### Tailwind Syntax
```
bg-white dark:bg-gray-900
text-gray-900 dark:text-white
border-gray-200 dark:border-gray-700
```

### User Preferences
```javascript
// Set dark mode
localStorage.setItem('darkMode', true)

// Read preference
const isDark = localStorage.getItem('darkMode') === 'true'
```

---

## Accessibility Features

### Focus Indicators
```
:focus {
    outline: 2px solid #6366f1;
    outline-offset: 2px;
}
```

### High Contrast
- Text contrast ratio ≥ 4.5:1 (WCAG AA)
- Colors not only indicator of state
- Icons paired with text labels

### Keyboard Navigation
- Tab through all interactive elements
- Clear focus indicators
- Logical tab order
- No keyboard traps

### Screen Readers
- Semantic HTML (header, main, footer, form)
- ARIA labels where needed
- Image alt text
- Skip navigation links

---

## Browser DevTools Tips

### Inspect Dark Mode
```javascript
// In browser console
document.documentElement.classList.add('dark')
document.documentElement.classList.remove('dark')
```

### Test Accessibility
```
DevTools > Lighthouse > Accessibility
DevTools > Elements > Accessibility Tree
Chrome > Accessibility Audit
```

### Test Responsiveness
```
DevTools > Device Toolbar (Ctrl+Shift+M)
Test at: 320px, 640px, 768px, 1024px, 1280px
Test on: iPhone, iPad, Android, Desktop
```

---

## Performance Metrics

### Load Time
- CSS: ~50KB (gzipped)
- JS: ~35KB (gzipped)
- Fonts: ~100KB (cached by browser)
- **Total**: ~185KB

### Core Web Vitals
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

---

Enjoy your beautifully designed Agentic AI interface! 🎨✨
