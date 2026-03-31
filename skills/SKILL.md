# Agent Skill: Advanced Website Builder

## Trigger
This skill is activated when a new `.txt` or `.md` file is processed from the `Inbox` queue that requires a website creation.

## Required Sub-Skills
When executing this skill, you MUST also load and follow these sub-skills:
1. [Design Aesthetics](file:///d:/practice/AI_Employee/skills/design_aesthetics.md) - For Premium UI standards.
2. [SEO & Optimization](file:///d:/practice/AI_Employee/skills/seo_optimization.md) - For performance and accessibility.
3. [Interactive Elements](file:///d:/practice/AI_Employee/skills/interactive_elements.md) - For dynamic functionality.

## Protocol

1. **Analyze Request**:
    - Read the instruction file.
    - Identify brand identity, target audience, and key features.

2. **Planning Phase**:
    - Select a layout that fits the request.
    - Reference colors and fonts from the [Design Aesthetics](file:///d:/practice/AI_Employee/skills/design_aesthetics.md) skill.

3. **Implementation Phase**:
    - **Structure**: Create a standard directory tree (`/css`, `/js`, `/images`).
    - **HTML**: Implement Semantic HTML following [SEO Optimization](file:///d:/practice/AI_Employee/skills/seo_optimization.md).
    - **CSS**: Apply modern styles from [Design Aesthetics](file:///d:/practice/AI_Employee/skills/design_aesthetics.md).
    - **JS**: Add interactivity guided by [Interactive Elements](file:///d:/practice/AI_Employee/skills/interactive_elements.md).

4. **Verification & Delivery**:
    - Run a final check against all three sub-skill checklists.
    - Ensure all files are linked correctly with relative paths.
