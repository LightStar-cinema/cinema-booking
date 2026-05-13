---
name: Cinematic Noir
colors:
  surface: '#15121b'
  surface-dim: '#15121b'
  surface-bright: '#3c3742'
  surface-container-lowest: '#100d16'
  surface-container-low: '#1d1a24'
  surface-container: '#221e28'
  surface-container-high: '#2c2833'
  surface-container-highest: '#37333e'
  on-surface: '#e8dfee'
  on-surface-variant: '#ccc3d8'
  inverse-surface: '#e8dfee'
  inverse-on-surface: '#332f39'
  outline: '#958da1'
  outline-variant: '#4a4455'
  surface-tint: '#d2bbff'
  primary: '#d2bbff'
  on-primary: '#3f008e'
  primary-container: '#7c3aed'
  on-primary-container: '#ede0ff'
  inverse-primary: '#732ee4'
  secondary: '#d3bbff'
  on-secondary: '#3f008d'
  secondary-container: '#5d03ca'
  on-secondary-container: '#c7aaff'
  tertiary: '#c3c0ff'
  on-tertiary: '#1d00a5'
  tertiary-container: '#564eec'
  on-tertiary-container: '#e6e3ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#eaddff'
  primary-fixed-dim: '#d2bbff'
  on-primary-fixed: '#25005a'
  on-primary-fixed-variant: '#5a00c6'
  secondary-fixed: '#ebddff'
  secondary-fixed-dim: '#d3bbff'
  on-secondary-fixed: '#250059'
  on-secondary-fixed-variant: '#5b00c5'
  tertiary-fixed: '#e2dfff'
  tertiary-fixed-dim: '#c3c0ff'
  on-tertiary-fixed: '#0f0069'
  on-tertiary-fixed-variant: '#3323cc'
  background: '#15121b'
  on-background: '#e8dfee'
  surface-variant: '#37333e'
typography:
  display-xl:
    fontFamily: Inter
    fontSize: 64px
    fontWeight: '800'
    lineHeight: 72px
    letterSpacing: -0.04em
  h1-cinematic:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  h2-cinematic:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  h3-cinematic:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.1em
  label-ui:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  xxl: 80px
  container-padding: 32px
  gutter: 24px
---

## Brand & Style

The design system is engineered to evoke the immersive, high-stakes atmosphere of a premium theater lobby. The brand personality is sophisticated, futuristic, and exclusive, targeting film enthusiasts who value a frictionless, high-end digital experience.

The visual style leverages **Glassmorphism** and **Vaporwave-inspired Futurism**. Depth is created through translucent layers and high-quality background blurs rather than traditional flat surfaces. The interface should feel like a "heads-up display" (HUD) for entertainment, utilizing glowing accents to guide user attention and reinforce a sense of digital luxury. High contrast between the deep obsidian backgrounds and vibrant neon interactive elements ensures a cinematic pop.

## Colors

The color palette is anchored in deep, "inkwell" blues and blacks to provide a canvas for light-based UI elements. 

- **Primary Range:** A spectrum of Violets and Indigos used for primary actions, branding, and active states.
- **Backgrounds:** A tiered system of dark blues. The base layer is nearly black, while surfaces use slightly lighter shades to suggest elevation.
- **Accents:** Neon Pink is reserved for high-urgency notifications or "VIP" status elements. Electric Blue is used for technical feedback, such as seat selection or loading states.
- **Gradients:** Use linear gradients (top-left to bottom-right) merging Indigo (#4F46E5) into Purple (#7C3AED) for premium components.

## Typography

This design system utilizes **Inter** for its incredible legibility and systematic feel across all body and heading sizes. To add a futuristic, technical edge, **Space Grotesk** is used for labels, UI metadata, and ticket details.

Headings should be set with tight letter spacing to appear dense and impactful. "Display" sizes should use a subtle text-shadow (0px 0px 20px rgba(124, 58, 237, 0.5)) to create a glowing effect against the dark background. Body text maintains generous line height to ensure readability in low-light environments.

## Layout & Spacing

The layout philosophy follows a **Fluid Grid** approach within a maximum container width of 1440px. Spacing is based on a 4px baseline grid to ensure mathematical harmony.

- **Margins:** Large viewport margins (32px to 48px) create a gallery-like feel.
- **Gutters:** Standardized at 24px to allow glass panels enough breathing room for their blur effects to be visible.
- **Z-Padding:** Elements using glassmorphism should have increased internal padding (minimum 24px) to prevent content from feeling crowded against the translucent edges.

## Elevation & Depth

Depth is not achieved through traditional shadows, but through **Backdrop Blurs** and **Luminescent Borders**.

1.  **Level 0 (Base):** #0B1120. Solid, no blur.
2.  **Level 1 (Cards/Panels):** Surface #111827 at 70% opacity with a 20px backdrop-blur. A 1px border of white at 10% opacity.
3.  **Level 2 (Modals/Popovers):** Surface #1F2937 at 80% opacity with a 40px backdrop-blur. A 1px border using a linear gradient of Primary/Secondary colors.
4.  **Glows:** Interactive elements (buttons, active seats) utilize an "Outer Glow" effect—a box-shadow with a large spread and low opacity using the element's primary color.

## Shapes

The design system uses a **Rounded** shape language to offset the sharp, futuristic color palette, making the interface feel premium and approachable.

- **Standard Elements (Inputs, Buttons):** 12px (radius_md).
- **Large Containers (Cards, Modals):** 24px (radius_lg).
- **Interactive Small Elements (Chips, Seat Icons):** 8px or Pill-shaped.
- **Glass Panels:** Must always use at least 12px rounding to maintain the "frosted pane" aesthetic.

## Components

### Buttons
- **Solid:** Gradient background (Indigo to Purple), white text, subtle glow on hover.
- **Glass:** Translucent background (10% white), 20px blur, 1px border. Hover state increases border opacity.
- **Glowing:** Reserved for "Book Now." Neon Pink border with a matching drop-shadow glow.

### Form Inputs
- **Style:** Underlined or fully enclosed glass frames. 
- **Focus State:** Border changes to Electric Blue with a subtle 4px glow. Placeholder text is low-contrast (30% white).

### Cards
- **Movie Posters:** Aspect ratio 2:3. On hover, show a glass overlay with "Quick View" and "Trailer" buttons.
- **Ticket Cards:** Perforated edge visual. Uses a glass background with a high-contrast white QR code.
- **Widgets:** Minimalist data containers with 1px muted borders.

### Navigation
- **Navbar:** Fixed to top, 100% width glass panel with a 20px blur. 1px bottom border (#ffffff10).
- **Sidebar:** Floating glass vertical panel with 24px rounded corners. Active states indicated by a vertical neon line.

### Seats
- **Standard:** Dark grey frame, stroke only.
- **Premium:** Purple fill, 50% opacity.
- **VIP:** Neon Pink glow, solid fill.
- **Selected:** Electric Blue solid fill with a pulsing glow effect.

### Data Visualization
- **Charts:** Use thin, glowing lines (Neon Pink or Electric Blue).
- **Area Charts:** Use 10% opacity fills under the lines to maintain transparency.
- **Grid Lines:** Minimal, using #ffffff05 opacity.

### QR Ticket
- **Container:** High-gloss white card (inverted from theme) for maximum scannability, encased in a larger dark glass modal.
- **Details:** Use Space Grotesk for the "Row/Seat/Theater" metadata to give a technical look.