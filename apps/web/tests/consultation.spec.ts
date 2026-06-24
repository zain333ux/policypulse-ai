import { expect, test } from "@playwright/test";

test("loads the sample, analyzes it, and opens exact evidence", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Load verified sample" }).click();
  await expect(page.getByText("10 comments detected")).toBeVisible();

  await page.getByRole("button", { name: "Analyze policy" }).click();
  await expect(page).toHaveURL(/\/analysis\//);
  await expect(page.getByText("Comments analyzed")).toBeVisible({ timeout: 15_000 });
  await expect(page.getByText("Concerned but constructive")).toBeVisible();

  await page.getByRole("button", { name: "COM-001" }).click();
  await expect(page.getByRole("heading", { name: "Source detail" }).filter({ visible: true })).toBeVisible();
  await expect(
    page.getByText(/automatic exam ban is too harsh without an appeal/).filter({ visible: true }),
  ).toBeVisible();
});

test("generates a survey blueprint and exposes the Google Forms workflow", async ({ page }) => {
  await page.route("**/v1/surveys/generate", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        schema_version: "1.0",
        title: "Attendance Policy Consultation",
        description: "Share your views on the proposed attendance policy.",
        policy_summary: "The draft proposes an 85 percent attendance threshold.",
        sections: [
          {
            title: "Policy impact",
            description: "Assess the proposed rule.",
            questions: Array.from({ length: 4 }, (_, index) => ({
              id: `Q-00${index + 1}`,
              question: `Impact question ${index + 1}?`,
              type: "paragraph",
              options: [],
              required: index === 0,
              purpose: "Understand likely impact.",
              scale_min: null,
              scale_max: null,
              scale_min_label: null,
              scale_max_label: null,
            })),
          },
          {
            title: "Improvements",
            description: "Suggest changes.",
            questions: Array.from({ length: 4 }, (_, index) => ({
              id: `Q-00${index + 5}`,
              question: `Improvement question ${index + 1}?`,
              type: "paragraph",
              options: [],
              required: false,
              purpose: "Collect improvements.",
              scale_min: null,
              scale_max: null,
              scale_min_label: null,
              scale_max_label: null,
            })),
          },
        ],
        sharing_message: "Please complete the policy consultation.",
        estimated_minutes: 6,
        generated_at: new Date().toISOString(),
      }),
    });
  });

  await page.goto("/survey");
  await page.getByRole("button", { name: "Load sample policy" }).click();
  await page.getByRole("button", { name: "Generate survey blueprint" }).click();

  await expect(page.getByText("Attendance Policy Consultation")).toBeVisible();
  await expect(page.getByRole("button", { name: "Create Google Form" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Blank CSV template" })).toBeVisible();
});

test("navigates findings and downloads both report formats", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Load verified sample" }).click();
  await page.getByRole("button", { name: "Analyze policy" }).click();
  await expect(page.getByText("Comments analyzed")).toBeVisible({ timeout: 15_000 });

  await page.getByRole("button", { name: "Policy gaps" }).click();
  await expect(page.getByText("No formal appeal or correction process")).toBeVisible();

  const markdown = page.waitForEvent("download");
  await page.getByRole("button", { name: "Markdown" }).click();
  expect((await markdown).suggestedFilename()).toBe("policypulse-report.md");

  const pdf = page.waitForEvent("download");
  await page.getByRole("button", { name: "PDF report" }).click();
  expect((await pdf).suggestedFilename()).toBe("policypulse-report.pdf");
});

test("theme control works and the layout does not overflow", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Toggle color theme" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflow).toBe(false);
});
