/** @odoo-module **/

import { registry } from "@web/core/registry";

const reminderNotificationService = {
    dependencies: ["notification", "orm"],
    start(env, { notification, orm }) {
        orm.searchRead(
            "payment.reminder.notification",
            [["is_read", "=", false]],
            ["message"],
            { limit: 10, order: "create_date desc" }
        ).then((records) => {
            if (!records.length) {
                return;
            }

            const closers = [];

            const closeAll = () => {
                closers.forEach((close) => {
                    try {
                        close();
                    } catch (e) {
                        // toast already closed, ignore
                    }
                });
                // Note: intentionally NOT marking as read here.
                // This only dismisses the toasts from the screen;
                // they will reappear on the next refresh since they
                // remain unread in the database.
            };

            records.forEach((rec) => {
                const close = notification.add(rec.message, {
                    type: "warning",
                    title: "Payment Reminder",
                    sticky: true,
                    buttons: [
                        {
                            name: "Close All",
                            onClick: () => closeAll(),
                        },
                    ],
                });
                closers.push(close);
            });
        }).catch(() => {});
        return {};
    },
};

registry.category("services").add("reminderNotificationService", reminderNotificationService);