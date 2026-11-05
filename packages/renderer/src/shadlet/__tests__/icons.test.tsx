import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ShadletIcon } from "@/shadlet/icons";

describe("generated icon registry", () => {
  it("renders common icons synchronously", () => {
    render(<ShadletIcon name="home" label="home" size={20} />);
    const icon = screen.getByLabelText("home");
    expect(icon.tagName.toLowerCase()).toBe("svg");
    expect(icon).toHaveAttribute("width", "20");
    expect(icon.querySelectorAll("path").length).toBeGreaterThan(0);
  });

  it("loads the complete catalogue lazily, including aliases", async () => {
    render(<ShadletIcon name="arrow-up-right" label="open link" />);
    await waitFor(() => {
      const icon = screen.getByLabelText("open link");
      expect(icon.querySelectorAll("path").length).toBeGreaterThan(0);
    });

    render(<ShadletIcon name="home" label="alias home" />);
    expect(screen.getByLabelText("alias home")).toBeInTheDocument();
  });
});
