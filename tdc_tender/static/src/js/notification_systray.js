/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import {
    Component,
    useState,
    useRef,
    onWillStart,
    onMounted,
    onWillUnmount,
    useExternalListener,
} from "@odoo/owl";

export class TenderNotificationSystray extends Component {
    static template = "tdc_tender.NotificationSystray";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.root = useRef("root");

        this.state = useState({
            open: false,
            count: 0,
            notifications: [],
        });

        onWillStart(async () => {
            await this.loadNotifications();
        });

        onMounted(() => {
            // Refresh the badge every 60 seconds
            this.interval = setInterval(() => this.loadNotifications(), 60000);
        });

        onWillUnmount(() => {
            clearInterval(this.interval);
        });

        // Close the panel when clicking anywhere outside it
        useExternalListener(window, "click", (ev) => {
            if (this.state.open && this.root.el && !this.root.el.contains(ev.target)) {
                this.state.open = false;
            }
        });
    }

    toggle(ev) {
        ev.stopPropagation();
        this.state.open = !this.state.open;
        if (this.state.open) {
            this.loadNotifications();
        }
    }

    async loadNotifications() {
        // Wrapped in try/catch on purpose: if this ever fails (network hiccup,
        // permissions, etc.) it must never take down the rest of the backend.
        try {
            this.state.count = await this.orm.call(
                "tdc.tender.notification",
                "get_unread_count",
                []
            );
            this.state.notifications = await this.orm.searchRead(
                "tdc.tender.notification",
                [["state", "=", "unread"]],
                ["name", "message", "notification_type", "priority", "due_date"],
                { limit: 5, order: "notification_date desc" }
            );
        } catch (error) {
            console.error("Tender notification systray failed to load:", error);
        }
    }

    async openNotification(id) {
        this.state.open = false;
        try {
            const action = await this.orm.call(
                "tdc.tender.notification",
                "action_open_record",
                [[id]]
            );
            if (action) {
                this.action.doAction(action);
            }
        } catch (error) {
            console.error("Tender notification failed to open:", error);
        }
    }

    viewDetail() {
        this.state.open = false;
        // Opens the exact same "Notifications" page as before
        this.action.doAction("tdc_tender.action_tdc_tender_notification");
    }
}

registry.category("systray").add(
    "tdc_tender.NotificationSystray",
    { Component: TenderNotificationSystray },
    { sequence: 1 }
);
