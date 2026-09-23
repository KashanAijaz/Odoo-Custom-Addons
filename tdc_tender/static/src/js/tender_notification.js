/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { useDropdownState } from "@web/core/dropdown/dropdown_hooks";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";

const TOAST_TYPE = { "2": "danger", "1": "info", "0": "success" };
const MAX_TOASTS = 5;
const COUNT_REFRESH_MS = 5 * 60 * 1000;   // bell count har 5 minute
const REMINDER_MS = 30 * 60 * 1000;       // popup reminder har 30 minute
let toastsShownThisLoad = false;          // refresh par sirf ek dafa pehla popup


export class TenderNotificationSystray extends Component {
    static template = "tdc_tender.TenderNotificationSystray";
    static components = { Dropdown };
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dropdown = useDropdownState();
        this.state = useState({ items: [], activeCount: 0 });
        this.activeToasts = new Map(); // key -> close function, duplicate rokne ke liye

        onMounted(async () => {
            await this.load();
            this.showToasts();
            this.timer = setInterval(() => this.load(), COUNT_REFRESH_MS);
            this.reminderTimer = setInterval(async () => {
                await this.load();
                this.showToasts(true);
            }, REMINDER_MS);
        });

        onWillUnmount(() => {
            clearInterval(this.timer);
            clearInterval(this.reminderTimer);
        });
    }

    async load() {
        const calls = [
            this.orm.call("tdc.upcoming.tender", "get_due_notifications", []).catch(() => []),
            this.orm.call("tdc.earnest.money", "get_due_notifications", []).catch(() => []),
            this.orm.call("tdc.performance.bond", "get_due_notifications", []).catch(() => []),
        ];
        const [tenders, earnest, bonds] = await Promise.all(calls);
        const items = [...tenders, ...earnest, ...bonds];
        items.sort((a, b) => a.days_left - b.days_left);
        this.state.items = items;
    }

    showToasts(isReminder = false) {
        if (!isReminder) {
            if (toastsShownThisLoad) {
                return;
            }
            toastsShownThisLoad = true;
        }
        // reminder mein sirf urgent items (kal, aaj ya overdue)
        const items = isReminder
            ? this.state.items.filter((n) => n.days_left <= 1)
            : this.state.items;

        items.slice(0, MAX_TOASTS).forEach((n) => {
            const key = `${n.model}-${n.id}-${isReminder ? "r" : "n"}`;
            // agar isi tender ka popup pehle se screen par hai to dobara mat dikhao
            if (this.activeToasts.has(key)) {
                return;
            }

            const close = this.notification.add(
                `${n.tender_title} (${n.partner}) — ${n.message}`,
                {
                    title: `${isReminder ? "⏰ Reminder: " : ""}${n.name} • ${n.priority_label}`,
                    type: TOAST_TYPE[n.priority] || "info",
                    className: n.priority === "gray" ? "tdc_toast_gray" : "",
                    sticky: true,
                    buttons: [
                        {
                            name: "Open",
                            primary: true,
                            onClick: () => this.openTender(n),
                        },
                    ],
                    onClose: () => {
                        this.activeToasts.delete(key);
                        this.state.activeCount = this.activeToasts.size;
                    },
                }
            );

            this.activeToasts.set(key, close);
            this.state.activeCount = this.activeToasts.size;
        });
    }

    clearAllToasts() {
        for (const close of this.activeToasts.values()) {
            close();
        }
        this.activeToasts.clear();
        this.state.activeCount = 0;
    }

    closeMenu() {
        this.dropdown.close();
    }

    async viewAll() {
        this.dropdown.close();
        await this.action.doAction({
            type: "ir.actions.client",
            tag: "tdc_tender_notification_list",
            name: "All Notifications",
        });
    }

    hasModel(model) {
        return this.state.items.some((n) => n.model === model);
    }

    async openTender(n) {
        this.dropdown.close();
        const nameMap = {
            "tdc.upcoming.tender": "Upcoming Tender",
            "tdc.earnest.money": "Earnest Money",
            "tdc.performance.bond": "Performance Bond",
        };
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: nameMap[n.model] || "Record",
            res_model: n.model,
            res_id: n.id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

// sequence 26 = messages icon (25) ke bilkul left mein
registry
    .category("systray")
    .add("tdc_tender_notification", { Component: TenderNotificationSystray }, { sequence: 26 });