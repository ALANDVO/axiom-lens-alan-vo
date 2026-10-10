import { describe, expect, it } from "vitest";

import {
  captureAccessibility,
  captureFrames,
  captureResources,
  isUninformativeFrameUrl,
} from "./CdpCaptureDocuments.js";

const origin = "https://app.example.test";

describe("CDP document capture", () => {
  it("walks deeply nested frame trees and returns every frame and resource", () => {
    let frameTree: Record<string, unknown> = {
      frame: { id: "frame-0", url: `${origin}/0` },
      resources: [{ url: `${origin}/0.js`, type: "Script" }],
    };
    for (let index = 1; index < 2_000; index += 1) {
      frameTree = {
        frame: {
          id: `frame-${String(index)}`,
          url: `${origin}/${String(index)}`,
        },
        resources: [{ url: `${origin}/${String(index)}.js`, type: "Script" }],
        childFrames: [frameTree],
      };
    }
    const result = { frameTree };
    const frames = captureFrames(result, new Set([origin]));
    const resources = captureResources(result, new Set([origin]));
    expect(frames.items).toHaveLength(2_000);
    expect(resources.items).toHaveLength(2_000);
  });

  it("retains full approved accessibility text", () => {
    const capture = captureAccessibility(
      [
        {
          nodes: [
            {
              nodeId: "node-1",
              role: { value: "button" },
              name: { value: "😀a" },
              description: { value: "éé" },
              childIds: ["missing-child"],
              properties: [
                { name: "disabled", value: { value: true } },
                { name: "valuetext", value: { value: "private value" } },
              ],
            },
          ],
        },
      ],
      {
        includeText: true,
      },
    );

    expect(capture.nodes[0]).toMatchObject({
      name: "😀a",
      description: "éé",
      states: [{ name: "disabled", value: true }],
    });
    expect(capture.treeIncomplete).toBe(true);
    expect(capture.textCapture).toEqual({
      status: "included",
      retained_bytes: 9,
      excluded_fields: 0,
    });
  });

  it("counts accessibility fields omitted without text approval", () => {
    const capture = captureAccessibility(
      [
        {
          nodes: [
            {
              nodeId: "node-1",
              name: { value: "private name" },
              description: { value: "private description" },
            },
          ],
        },
      ],
      {
        includeText: false,
      },
    );

    expect(capture.nodes[0]).toMatchObject({ name: null, description: null });
    expect(capture.textCapture).toEqual({
      status: "not_approved",
      retained_bytes: 0,
      excluded_fields: 2,
    });
  });
});

describe("isUninformativeFrameUrl — Chromium 150 opaque placeholder regression (issue #1384)", () => {
  // Regression: Chromium 150 reports ":" from Page.getFrameTree for a
  // committed, fully loaded same-origin page. Before the fix this caused
  // inspect_web_page to throw target_not_allowed for every allowed target.
  it('Chromium 150 opaque frame-tree placeholder ":" is uninformative', () => {
    expect(isUninformativeFrameUrl(":")).toBe(true);
  });

  it("undefined frame URL is uninformative", () => {
    expect(isUninformativeFrameUrl(undefined)).toBe(true);
  });

  it("empty string frame URL is uninformative", () => {
    expect(isUninformativeFrameUrl("")).toBe(true);
  });

  it('"about:blank" is uninformative', () => {
    expect(isUninformativeFrameUrl("about:blank")).toBe(true);
  });

  it('"about:srcdoc" is uninformative', () => {
    expect(isUninformativeFrameUrl("about:srcdoc")).toBe(true);
  });

  it("chrome-extension URL is uninformative (non-http scheme)", () => {
    expect(
      isUninformativeFrameUrl("chrome-extension://abc/page.html"),
    ).toBe(true);
  });

  it("real http URL is informative", () => {
    expect(
      isUninformativeFrameUrl("http://127.0.0.1:3000/app?probe=1"),
    ).toBe(false);
  });

  it("real https URL is informative", () => {
    expect(isUninformativeFrameUrl("https://app.example.test/page")).toBe(
      false,
    );
  });
});
