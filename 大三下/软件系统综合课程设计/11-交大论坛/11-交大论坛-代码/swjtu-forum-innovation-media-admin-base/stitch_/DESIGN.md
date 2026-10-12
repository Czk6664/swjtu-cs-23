---
name: Academic Nexus
colors:
  surface: '#f7f9fc'
  surface-dim: '#d8dadd'
  surface-bright: '#f7f9fc'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f7'
  surface-container: '#eceef1'
  surface-container-high: '#e6e8eb'
  surface-container-highest: '#e0e3e6'
  on-surface: '#191c1e'
  on-surface-variant: '#414751'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f4'
  outline: '#717782'
  outline-variant: '#c1c7d3'
  surface-tint: '#0060a8'
  primary: '#004e8a'
  on-primary: '#ffffff'
  primary-container: '#0066b2'
  on-primary-container: '#d1e3ff'
  inverse-primary: '#a2c9ff'
  secondary: '#536069'
  on-secondary: '#ffffff'
  secondary-container: '#d6e4ef'
  on-secondary-container: '#59666f'
  tertiary: '#005656'
  on-tertiary: '#ffffff'
  tertiary-container: '#007070'
  on-tertiary-container: '#6bf6f6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d3e4ff'
  primary-fixed-dim: '#a2c9ff'
  on-primary-fixed: '#001c38'
  on-primary-fixed-variant: '#004881'
  secondary-fixed: '#d6e4ef'
  secondary-fixed-dim: '#bac8d3'
  on-secondary-fixed: '#101d25'
  on-secondary-fixed-variant: '#3b4851'
  tertiary-fixed: '#6bf7f7'
  tertiary-fixed-dim: '#48dada'
  on-tertiary-fixed: '#002020'
  on-tertiary-fixed-variant: '#004f50'
  background: '#f7f9fc'
  on-background: '#191c1e'
  surface-variant: '#e0e3e6'
typography:
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.6'
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1'
  metadata:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  container-max: 1200px
  gutter: 1.5rem
  margin-mobile: 1rem
  card-padding: 1.25rem
  stack-gap: 0.75rem
---

## Brand & Style

The design system is engineered to support an academic community that balances formal institutional values with the dynamic energy of student life. The brand personality is **authoritative yet accessible**, fostering a safe and structured environment for knowledge exchange, campus news, and peer support.

The visual direction follows a **Modern Corporate** aesthetic with a heavy emphasis on **Information Density and Clarity**. Drawing from the provided reference, the system utilizes a high-ratio of white space, a structured blue-based hierarchy, and subtle depth cues to ensure that content-heavy forum pages remain legible and non-intimidating. The emotional response should be one of reliability and calm focus.

## Colors

The palette is rooted in a stable, "University Blue" to establish institutional trust. 

- **Primary Blue:** Used for high-priority actions (CTA), active navigation states, and branding elements.
- **Secondary Blue:** A soft wash used for background highlights, active pill states, and low-priority containers.
- **Surface & Neutrals:** A range of cool grays and pure whites maintain a clean, academic feel. Backgrounds use a very light gray to differentiate the page from white content cards.
- **Accents:** A muted teal is reserved for category tags, verification badges, and status indicators to provide subtle visual variety without breaking the professional tone.

## Typography

Typography is optimized for Chinese and Latin character legibility. **Plus Jakarta Sans** provides a modern, friendly geometric touch for headings, while **Inter** serves as the workhorse for high-density body text and metadata.

- **Headlines:** Use high weight (600-700) and tighter line heights to create strong visual anchors for post titles and section headers.
- **Body:** Generous line heights (1.6) are applied to forum posts to prevent eye fatigue during long reading sessions.
- **Metadata:** Smaller, lower-contrast styles are used for timestamps, view counts, and secondary user info, ensuring they don't compete with the primary content.

## Layout & Spacing

The system uses a **Fixed Grid** approach for desktop (max-width 1200px) to maintain a centered, editorial feel, transitioning to a fluid layout for mobile devices.

- **Grid:** A 12-column grid is standard, with sidebars typically occupying 3-4 columns and the main feed occupying 8-9 columns.
- **Rhythm:** An 8px base unit drives all spacing.
- **Density:** Card padding is kept generous (20px) to allow content to "breathe," reflecting an organized and thoughtful environment rather than a cluttered social feed.

## Elevation & Depth

Visual hierarchy is primarily achieved through **Tonal Layers** and **Soft Ambient Shadows**.

- **Surfaces:** Main content cards sit on a `#FFFFFF` surface against a `#F5F7FA` background. 
- **Depth:** Shadows are extremely subtle, using a large blur radius (12px to 20px) with very low opacity (approx. 4-6%) and a slight blue tint (`#004488`) to maintain harmony with the primary color palette.
- **Interaction:** Hovering over a post card should slightly increase the shadow's spread or add a subtle 1px border in the primary color to indicate interactivity.

## Shapes

The shape language is **Rounded (Level 2)**. This strikes a balance between the geometric rigor of an academic institution and the modern, friendly feel of a community-led platform.

- **Standard Elements:** Buttons, input fields, and small chips use a 0.5rem (8px) radius.
- **Containers:** Post cards and section navigation containers use a 1rem (16px) radius to create a soft, welcoming frame for the content.
- **Search:** Search bars and specific pill-style navigation items use a fully rounded (capsule) shape to differentiate them as global utility elements.

## Components

### Post Cards
Cards are the primary content unit. They feature a white background, 16px corner radius, and a subtle border or shadow. Titles are prominent (Headline-sm), followed by a brief text preview and a footer containing metadata (user, time, tags) and engagement actions.

### Navigation Pills
Used for filtering forum categories. Active states use the **Secondary Blue** background with **Primary Blue** text, while inactive states remain neutral with a light gray background.

### Search Bar
A prominent capsule-shaped input. It should feature a subtle inner shadow or a light gray stroke. The search icon should be low-contrast until the field is focused.

### User Badges
Avatar displays include a circular profile image and a small "level" or "department" badge. Department tags use the **Tertiary Teal** for clear differentiation from interaction buttons.

### Primary Action Button
The "Post" or "Create" button should be high-contrast (Primary Blue) with white text, using a subtle drop shadow to indicate its importance as the primary engagement driver.