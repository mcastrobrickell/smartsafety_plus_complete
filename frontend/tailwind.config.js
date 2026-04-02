/** @type {import('tailwindcss').Config} */
module.exports = {
    darkMode: ["class"],
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
        "./public/index.html"
    ],
    theme: {
        extend: {
            fontFamily: {
                'display': ['Outfit', 'sans-serif'],
                'body': ['IBM Plex Sans', 'sans-serif'],
            },
            colors: {
                // Dark-Tech Custom Colors
                'dark-bg': '#05070A',
                'dark-surface': '#0A0F1A',
                'dark-input': '#111827',
                'dark-elevated': '#1E293B',
                'cyan-accent': '#00E5FF',
                'blue-secondary': '#2563EB',
                'success-green': '#22C55E',
                
                // Shadcn Colors
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                chart: {
                    '1': 'hsl(var(--chart-1))',
                    '2': 'hsl(var(--chart-2))',
                    '3': 'hsl(var(--chart-3))',
                    '4': 'hsl(var(--chart-4))',
                    '5': 'hsl(var(--chart-5))'
                }
            },
            borderRadius: {
                lg: 'var(--radius)',
                md: 'calc(var(--radius) - 2px)',
                sm: 'calc(var(--radius) - 4px)'
            },
            boxShadow: {
                'glow-cyan': '0 0 20px rgba(0, 229, 255, 0.3)',
                'glow-cyan-lg': '0 0 40px rgba(0, 229, 255, 0.4)',
                'glow-blue': '0 0 20px rgba(37, 99, 235, 0.3)',
                'card-dark': '0 4px 24px rgba(0, 0, 0, 0.4)',
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'gradient-tech': 'linear-gradient(135deg, #00E5FF 0%, #2563EB 100%)',
                'gradient-card': 'linear-gradient(145deg, rgba(10, 15, 26, 0.95), rgba(17, 24, 39, 0.9))',
            },
            keyframes: {
                'accordion-down': {
                    from: { height: '0' },
                    to: { height: 'var(--radix-accordion-content-height)' }
                },
                'accordion-up': {
                    from: { height: 'var(--radix-accordion-content-height)' },
                    to: { height: '0' }
                },
                'glow-pulse': {
                    '0%, 100%': { boxShadow: '0 0 20px rgba(0, 229, 255, 0.2)' },
                    '50%': { boxShadow: '0 0 40px rgba(0, 229, 255, 0.4)' }
                },
                'fade-in': {
                    from: { opacity: '0', transform: 'translateY(10px)' },
                    to: { opacity: '1', transform: 'translateY(0)' }
                }
            },
            animation: {
                'accordion-down': 'accordion-down 0.2s ease-out',
                'accordion-up': 'accordion-up 0.2s ease-out',
                'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
                'fade-in': 'fade-in 0.4s ease-out'
            }
        }
    },
    plugins: [require("tailwindcss-animate")],
};
