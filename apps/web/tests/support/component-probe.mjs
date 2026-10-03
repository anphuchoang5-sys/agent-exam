// Actual-TSX state probes, deliberately not a React DOM/browser renderer.
import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";
import ts from "typescript";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
export function deferred() {
  let resolve, reject;
  const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
export async function flush() { for (let i = 0; i < 12; i++) await Promise.resolve(); }
export function nodes(tree) {
  if (Array.isArray(tree)) return tree.flatMap(nodes);
  if (!tree || typeof tree !== "object") return [];
  return [tree, ...nodes(tree.props?.children)];
}
export function text(tree) {
  if (Array.isArray(tree)) return tree.map(text).join("");
  if (tree == null || typeof tree === "boolean") return "";
  return typeof tree === "object" ? text(tree.props?.children) : String(tree);
}
export function find(tree, name) {
  const match = nodes(tree).find((node) => typeof node.type === "function"
    ? node.type.name === name : node.type === "button" && text(node) === name);
  if (!match) throw new Error(`Missing ${name}`);
  return match;
}
export function probe(path, props = {}, overrides = {}, href = "https://example.test/?view=jobs&job=old") {
  const slots = []; const effects = []; const modules = new Map();
  let cursor = 0, pendingEffects = [], rendered;
  const same = (a, b) => a && b && a.length === b.length && a.every((item, i) => Object.is(item, b[i]));
  const react = {
    useState(initial) {
      const i = cursor++;
      if (!(i in slots)) slots[i] = typeof initial === "function" ? initial() : initial;
      return [slots[i], (value) => { slots[i] = typeof value === "function" ? value(slots[i]) : value; }];
    },
    useRef(initial) {
      const i = cursor++; return slots[i] ??= { current: initial };
    },
    useCallback(fn, dependencies) {
      const i = cursor++;
      if (!same(slots[i]?.dependencies, dependencies)) slots[i] = { fn, dependencies };
      return slots[i].fn;
    },
    useEffect(effect, dependencies) {
      const i = cursor++;
      if (!same(effects[i]?.dependencies, dependencies)) pendingEffects.push(() => {
        effects[i]?.cleanup?.();
        effects[i] = { dependencies, cleanup: effect() };
      });
    },
  };
  const window = {
    location: { href, pathname: new URL(href).pathname },
    history: { replaceState(_state, _title, url) {
      window.location.href = new URL(url, window.location.href).href;
    } },
    addEventListener() {}, removeEventListener() {},
  };
  const jsx = (type, props, key) => ({ type, props, key });
  function load(filename) {
    if (modules.has(filename)) return modules.get(filename);
    const exports = {}; modules.set(filename, exports);
    const require = (specifier) => {
      if (specifier === "react") return react;
      if (specifier === "react/jsx-runtime") return { jsx, jsxs: jsx, Fragment: "fragment" };
      const base = resolve(dirname(filename), specifier);
      const candidate = [base + ".ts", base + ".tsx"].find(existsSync);
      if (!candidate) throw new Error(`Unsupported probe import ${specifier}`);
      const relative = candidate.slice(root.length + 1).replaceAll("\\", "/");
      return { ...load(candidate), ...overrides[relative] };
    };
    const { outputText } = ts.transpileModule(readFileSync(filename, "utf8"), { compilerOptions: {
      module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX,
    } });
    vm.runInNewContext(outputText, {
      exports, require, window, URL, URLSearchParams, crypto: globalThis.crypto, console,
    }, { filename });
    return exports;
  }
  const Component = load(resolve(root, path)).default;
  return {
    window,
    get tree() { return rendered; },
    getModule: (path) => load(resolve(root, path)),
    render(next = props) {
      props = next; cursor = 0; pendingEffects = []; rendered = Component(props);
      pendingEffects.forEach((effect) => effect()); return rendered;
    },
    unmount() { effects.forEach((effect) => effect?.cleanup?.()); },
  };
}
