/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart } from "@odoo/owl";

export class TenderNotificationListAction extends Component {
    static template = "tdc_tender.TenderNotificationListAction";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ items: [] });

        onWillStart(async () => {
            await this.load();
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

    async openRecord(n) {
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

registry.category("actions").add("tdc_tender_notification_list", TenderNotificationListAction);