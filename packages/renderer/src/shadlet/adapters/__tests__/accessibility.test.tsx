import { render } from "@testing-library/react";
import axe from "axe-core";
import { describe, expect, it } from "vitest";
import type { ShadletNode } from "@/protocol/schema";
import { TreeRenderer } from "@/runtime/tree";

function node(
  id: string,
  type: string,
  props: Record<string, unknown> = {},
  children: ShadletNode[] = [],
): ShadletNode {
  return { id, type, props, children, events: {}, slots: {}, text: null };
}

function textNode(id: string, text: string): ShadletNode {
  return {
    id,
    type: "#text",
    props: {},
    children: [],
    events: {},
    slots: {},
    text,
  };
}

describe("built-in component accessibility", () => {
  it("has no WCAG 2.1 A/AA violations across representative component families", async () => {
    render(
      <TreeRenderer
        tree={node("root", "Column", {}, [
          node("heading", "Heading", { level: 1 }, [
            textNode("heading-text", "account settings"),
          ]),
          node("input", "Input", {
            type: "email",
            ariaLabel: "email address",
          }),
          node("textarea", "Textarea", { ariaLabel: "profile biography" }),
          node("checkbox", "Checkbox", { label: "receive updates" }),
          node("switch", "Switch", { label: "enable notifications" }),
          node("slider", "Slider", { ariaLabel: "volume" }),
          node("select", "Select", {
            ariaLabel: "account role",
            options: [{ value: "member", label: "member" }],
          }),
          node("native-select", "NativeSelect", {
            ariaLabel: "account status",
            options: [{ value: "active", label: "active" }],
          }),
          node("radio", "RadioGroup", {
            ariaLabel: "contact preference",
            options: [{ value: "email", label: "email" }],
          }),
          node("combobox", "Combobox", {
            ariaLabel: "timezone",
            options: [{ value: "utc", label: "utc" }],
          }),
          node("otp", "InputOTP", { ariaLabel: "verification code" }),
          node("button", "Button", {}, [
            textNode("button-text", "save settings"),
          ]),
          node("alert", "Alert", {
            title: "saved",
            description: "your settings were updated",
          }),
          node("progress", "Progress", { value: 50, label: "upload progress" }),
        ])}
        onEvent={() => {}}
        navigate={() => {}}
        route="/"
      />,
    );

    const results = await axe.run(document.body, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
      },
    });
    expect(results.violations).toEqual([]);
  });
});
