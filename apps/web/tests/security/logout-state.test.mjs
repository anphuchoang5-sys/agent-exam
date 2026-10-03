import assert from "node:assert/strict";
import test from "node:test";
import { find, flush, nodes, probe, text } from "../support/component-probe.mjs";

for (const code of ["DEPENDENCY_UNAVAILABLE", "UNAVAILABLE"]) {
  test(`logout ${code} remains visible while authenticated, then success clears URL and shell`, async () => {
    let ApiError, attempts = 0;
    const view = probe("src/features/identity/session.tsx", {}, {
      "src/lib/api-client.ts": {
        currentActor: async () => ({ user_id: "owner", username: "owner", role: "owner" }),
        logout: async () => { if (++attempts === 1) throw new ApiError(code); },
      },
    });
    ApiError = view.getModule("src/lib/api-client.ts").ApiError;
    view.render(); await flush(); view.render();
    await find(view.tree, "WorkbenchShell").props.signOut(); view.render();
    const shell = find(view.tree, "WorkbenchShell");
    assert.equal(shell.props.actor.username, "owner");
    const shellView = probe("src/features/workbench/shell.tsx", shell.props);
    shellView.render();
    const alert = nodes(shellView.tree).find((node) => node.props?.role === "alert");
    assert.ok(alert);
    assert.match(text(alert), /退出未完成/);
    assert.equal(find(shellView.tree, "退出登录").props.disabled, false);
    assert.match(view.window.location.href, /job=old/);
    await shell.props.signOut(); view.render();
    assert.equal(nodes(view.tree).some((node) => node.type?.name === "WorkbenchShell"), false);
    assert.equal(view.window.location.href, "https://example.test/");
  });
}
