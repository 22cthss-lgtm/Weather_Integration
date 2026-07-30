import { Extension } from "@tiptap/core";
import { CellSelection } from "@tiptap/pm/tables";


export function normalizeTableWidth(value) {
  const normalized = String(value ?? "").trim().toLowerCase();
  if (normalized === "auto") return "auto";
  return /^\d+$/.test(normalized) && Number(normalized) >= 25 && Number(normalized) <= 100
    ? normalized
    : null;
}

export function normalizeVerticalAlign(value) {
  const normalized = String(value ?? "").trim().toLowerCase();
  return ["top", "middle", "bottom"].includes(normalized) ? normalized : null;
}

export function calculateTableWidthPercent(startWidth, deltaX, containerWidth) {
  if (!Number.isFinite(containerWidth) || containerWidth <= 0) return 100;
  const percentage = Math.round(((startWidth + deltaX) / containerWidth) * 100);
  return Math.min(100, Math.max(25, percentage));
}

export function findActiveTable(state) {
  const { $from } = state.selection;
  for (let depth = $from.depth; depth > 0; depth -= 1) {
    const node = $from.node(depth);
    if (node.type.name === "table") {
      return { node, position: $from.before(depth) };
    }
  }
  return null;
}

export function getSelectedVerticalAlign(state) {
  const values = new Set();
  if (state.selection instanceof CellSelection) {
    state.selection.forEachCell((node) => values.add(node.attrs.verticalAlign || "top"));
  } else {
    const { $from } = state.selection;
    for (let depth = $from.depth; depth > 0; depth -= 1) {
      const node = $from.node(depth);
      if (["tableCell", "tableHeader"].includes(node.type.name)) {
        values.add(node.attrs.verticalAlign || "top");
        break;
      }
    }
  }
  return values.size === 1 ? [...values][0] : null;
}

const TableControls = Extension.create({
  name: "faqTableControls",

  addGlobalAttributes() {
    return [
      {
        types: ["table"],
        attributes: {
          tableWidth: {
            default: "auto",
            parseHTML: (element) => normalizeTableWidth(element.getAttribute("data-table-width")) || "auto",
            renderHTML: ({ tableWidth }) => {
              const width = normalizeTableWidth(tableWidth) || "auto";
              return {
                "data-table-width": width,
                ...(width === "auto" ? {} : { style: `width: ${width}%` }),
              };
            },
          },
        },
      },
      {
        types: ["tableCell", "tableHeader"],
        attributes: {
          verticalAlign: {
            default: "top",
            parseHTML: (element) => normalizeVerticalAlign(element.getAttribute("data-vertical-align")) || "top",
            renderHTML: ({ verticalAlign }) => ({ "data-vertical-align": normalizeVerticalAlign(verticalAlign) || "top" }),
          },
        },
      },
    ];
  },

  addCommands() {
    return {
      setTableWidth: (value) => ({ state, dispatch }) => {
        const normalized = normalizeTableWidth(value);
        const table = findActiveTable(state);
        if (!normalized || !table) return false;
        if (dispatch) {
          dispatch(state.tr.setNodeMarkup(table.position, undefined, {
            ...table.node.attrs,
            tableWidth: normalized,
          }));
        }
        return true;
      },
      setCellVerticalAlign: (value) => ({ commands }) => {
        const normalized = normalizeVerticalAlign(value);
        return normalized ? commands.setCellAttribute("verticalAlign", normalized) : false;
      },
    };
  },
});

export default TableControls;
