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
        this.state = useState({ items: [] });

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
        try {
            this.state.items = await this.orm.call(
                "tdc.upcoming.tender",
                "get_due_notifications",
                []
            );
        } catch (e) {
            // user ke paas access na ho to chup-chaap ignore
            this.state.items = [];
        }
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
            this.notification.add(`${n.tender_title} (${n.partner}) — ${n.message}`, {
                title: `${isReminder ? "⏰ Reminder: " : ""}${n.name} • ${n.priority_label}`,
                type: TOAST_TYPE[n.priority] || "info",
                sticky: true,
                buttons: [
                    {
                        name: "Open",
                        primary: true,
                        onClick: () => this.openTender(n),
                    },
                ],
            });
        });
    }

    closeMenu() {
        this.dropdown.close();
    }

    async viewAll() {
        this.dropdown.close();
        const action = await this.orm.call(
            "tdc.upcoming.tender",
            "action_open_due_tenders",
            []
        );
        await this.action.doAction(action);
    }

    async openTender(n) {
        this.dropdown.close();
        await this.action.doAction({
            type: "ir.actions.act_window",
            name: "Upcoming Tender",
            res_model: "tdc.upcoming.tender",
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