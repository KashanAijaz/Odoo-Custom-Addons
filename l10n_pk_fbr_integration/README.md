# l10n_pk_fbr_integration

Integrates Odoo 19 invoices with FBR Digital Invoicing (DI) APIs.

## Install
1. Place folder in Odoo addons path.
2. Restart Odoo server.
3. Update Apps list and install `Pakistan FBR Digital Invoicing`.

## Configure
- Go to Settings → FBR Digital Invoicing (Settings) and set:
  - FBR DI API URL (sandbox or production)
  - API Key and Secret
  - Sandbox mode
  - FBR Cookie String : if applicable
  - New addition of fields in product (HS Code, HS Unit of Measure)

## Usage
- Edit an invoice (Draft): you can call it by auto with invoice onchange. a light-weight tax estimate attempt will run when lines change (non-blocking).
- Use the **Sync with FBR** button to send full invoice to FBR; the response will populate FBR Invoice No and status.

## Important
- This module demonstrates the integration pattern. Adapt endpoints, signing, and JSON payload exactly as required by FBR technical documentation. See FBR DI technical spec. :contentReference[oaicite:2]{index=2}


Support
-------

For technical support, bug reports, or feature requests:
- **Email**: support@zalinotech.com
- **Website**: https://zalinotech.com
- **Issue Tracker**: GitHub Repository Issues

Company
-------

**Developed & Maintained by:**
`Zalino Tech Private Limited <https://zalinotech.com>`__

**Lead Development Team:**
- **Project Lead**: Zahid Anwar
- **Quality Assurance**: Zalino Tech QA Team
- **Technical Support**: Zalino Tech Support Team

License
-------

This module is licensed under the **Lesser General Public License v3.0 (LGPL-3)**.
For complete license details, visit: https://www.gnu.org/licenses/lgpl-3.0.en.html

Credits
-------

- **Lead Developer (v19):** Zahid Anwar
- **Lead Developer (v18):** Zahid Anwar
- **Contact:** info@zalinotech.com

Bug Reporting
-------------

Found an issue? Please report it through our GitHub Issue Tracker. Before submitting:
- Check existing issues to avoid duplicates
- Provide detailed reproduction steps
- Include Odoo version and module version
- Attach relevant screenshots or error logs

Maintainer
----------

.. image:: https://zalinotech.com/wp-content/uploads/2024/09/ZalinoLogo.png
   :alt: Zalino Tech Private Limited
   :target: https://zalinotech.com
   :width: 200
   :height: 60

**Zalino Tech Private Limited** specializes in Odoo customization, implementation, and support services. We provide enterprise-grade solutions tailored to your business needs.

- **Website**: https://zalinotech.com
- **Email**: info@zalinotech.com
- **Address**: Islamabad, Pakistan

Changelog
---------

**Version 1.0** (2025-09-23)
- Initial release for Odoo v19
- Multi-level approval workflow implementation
- Amount-based threshold configuration
- Approval history and audit trail
- Seamless integration with purchase module