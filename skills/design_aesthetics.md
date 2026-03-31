# Agent Skill: Design Aesthetics (Premium UI)

## Purpose
Ensure all generated websites have a "World-Class" premium feel with modern aesthetic standards.

## Principles
1. **Glassmorphism**: Use translucent backgrounds with backdrop-filter: blur() for cards and navbars.
2. **Typography**: Use Google Fonts (Inter, Roboto, or Outfit). Avoid default system fonts.
3. **Color Harmony**: Use HSL based color palettes. Primary, Secondary, and Accent colors should be consistent.
4. **Spacing**: Implement a strict 8px/16px grid system for margins and padding.
5. **Micro-animations**: Add subtle transition effects on hover and click (e.g., transition: all 0.3s ease).

## Implementation Checklist
- [ ] Import modern fonts at the top of CSS.
- [ ] Define root variables (--primary, --glass-bg, --glass-border, --text).
- [ ] Use border-radius: 12px or higher for a "Soft" modern look.
- [ ] Add box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1) for depth.
- [ ] Implement Dark Mode support using prefers-color-scheme.
