import { TableView } from "@tiptap/extension-table";

import { calculateTableWidthPercent, normalizeTableWidth } from "./TableControls";


export default class ResizableTableView extends TableView {
  constructor(node, cellMinWidth, view, HTMLAttributes = {}) {
    super(node, cellMinWidth, view, HTMLAttributes);
    this.view = view;
    this.dragState = null;
    this.handle = document.createElement("div");
    this.handle.className = "rte-table-width-handle";
    this.handle.contentEditable = "false";
    this.handle.setAttribute("role", "separator");
    this.handle.setAttribute("aria-label", "Resize table width");
    this.handle.setAttribute("aria-orientation", "vertical");
    this.handle.addEventListener("pointerdown", this.onPointerDown);
    this.dom.appendChild(this.handle);
    this.applyTableWidth(node);
  }

  applyTableWidth(node) {
    const width = normalizeTableWidth(node.attrs.tableWidth) || "auto";
    this.table.setAttribute("data-table-width", width);
    if (width !== "auto") {
      this.table.style.width = `${width}%`;
      this.handle.style.left = `${width}%`;
    } else {
      requestAnimationFrame(() => {
        this.handle.style.left = `${this.table.getBoundingClientRect().width}px`;
      });
    }
  }

  update(node) {
    const updated = super.update(node);
    if (updated) this.applyTableWidth(node);
    return updated;
  }

  onPointerDown = (event) => {
    event.preventDefault();
    event.stopPropagation();
    const container = this.dom.parentElement;
    this.dragState = {
      startX: event.clientX,
      startWidth: this.table.getBoundingClientRect().width,
      containerWidth: container?.getBoundingClientRect().width || 0,
    };
    this.dom.classList.add("is-resizing-table");
    document.addEventListener("pointermove", this.onPointerMove);
    document.addEventListener("pointerup", this.onPointerUp);
  };

  onPointerMove = (event) => {
    if (!this.dragState) return;
    const width = calculateTableWidthPercent(
      this.dragState.startWidth,
      event.clientX - this.dragState.startX,
      this.dragState.containerWidth,
    );
    this.table.style.width = `${width}%`;
    this.table.setAttribute("data-table-width", String(width));
    this.handle.style.left = `${width}%`;
  };

  onPointerUp = (event) => {
    if (this.dragState) {
      const width = calculateTableWidthPercent(
        this.dragState.startWidth,
        event.clientX - this.dragState.startX,
        this.dragState.containerWidth,
      );
      const tablePosition = this.view.posAtDOM(this.contentDOM, 0) - 1;
      const tableNode = this.view.state.doc.nodeAt(tablePosition);
      if (tableNode?.type.name === "table") {
        this.view.dispatch(this.view.state.tr.setNodeMarkup(tablePosition, undefined, {
          ...tableNode.attrs,
          tableWidth: String(width),
        }));
      }
    }
    this.stopDragging();
  };

  stopDragging() {
    this.dragState = null;
    this.dom.classList.remove("is-resizing-table");
    document.removeEventListener("pointermove", this.onPointerMove);
    document.removeEventListener("pointerup", this.onPointerUp);
  }

  destroy() {
    this.stopDragging();
    this.handle.removeEventListener("pointerdown", this.onPointerDown);
  }
}
