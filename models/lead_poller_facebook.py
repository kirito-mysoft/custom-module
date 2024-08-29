from odoo import models, api
import logging
import requests

_logger = logging.getLogger(__name__)


class LeadPoller(models.Model):
    _name = 'lead.poller'

    @api.model
    def poll_facebook_leads(self):
        _logger.info("Polling Facebook Leads")

        # Your Facebook API access token and page ID
        access_token = 'EAAGn5Al0joQBOZBWQCyU0ZCZBNDYGtZAf5uuSZBmL2lA8PKZAwZAesZAaWZCpzxhDryaLdW9mrQlik5WShgf0ZBZAOUHw8HLMVn9qcUyaIJMByLjZBZBC7UqCEijUeW3s6zPATQ4AakuZAkmiBMNS5GoCneOs6r8AWqBTmBUruTjKZAzDZBuyTrZCYOst0aTZBkzdamzjahETMimD79PqxmomQrx5Ax19kZB7oh'
        page_id = '410036575718217'
        form_url = f"https://graph.facebook.com/v20.0/{page_id}/leadgen_forms?access_token={access_token}"

        try:
            # Step 1: Fetch form IDs
            form_response = requests.get(form_url)
            if form_response.status_code == 200:
                forms = form_response.json().get('data', [])
                for form in forms:
                    form_id = form['id']
                    self.fetch_and_process_leads(form_id, access_token)
            else:
                _logger.error(f"Failed to fetch forms: {form_response.status_code} - {form_response.text}")
        except Exception as e:
            _logger.error(f"Error fetching Facebook forms: {str(e)}")

    def fetch_and_process_leads(self, form_id, access_token):
        lead_url = f"https://graph.facebook.com/v20.0/{form_id}/leads?access_token={access_token}"

        try:
            # Step 2: Fetch leads for the form ID
            lead_response = requests.get(lead_url)
            if lead_response.status_code == 200:
                leads = lead_response.json().get('data', [])
                for lead_data in leads:
                    self.process_facebook_lead(lead_data)
            else:
                _logger.error(
                    f"Failed to fetch leads for form {form_id}: {lead_response.status_code} - {lead_response.text}")
        except Exception as e:
            _logger.error(f"Error fetching leads for form {form_id}: {str(e)}")

    def process_facebook_lead(self, lead_data):
        try:
            # Extract relevant information from the lead data
            field_data = {field['name']: field['values'][0] for field in lead_data.get('field_data', [])}
            name = field_data.get('full_name')
            email = field_data.get('email')
            phone = field_data.get('phone_number')
            stage_name = 'facebook'  # Example: hardcoded or can be extracted if available
            customer_name = field_data.get('company_name')  # Assuming you have this information

            # Ensure all required fields are provided
            if not all([name, email, phone, stage_name, customer_name]):
                _logger.warning("Missing required fields in lead data")
                return

            # Find the stage ID based on the stage name
            stage = self.env['crm.stage'].sudo().search([('name', '=', stage_name)], limit=1)
            if not stage:
                _logger.warning(f"Stage '{stage_name}' not found")
                return

            # Check if customer exists
            customer = self.env['res.partner'].sudo().search([('name', '=', customer_name)], limit=1)
            if not customer:
                # Create a new customer if it doesn't exist
                customer = self.env['res.partner'].sudo().create({
                    'name': customer_name,
                    'email': email,
                    'phone': phone,
                })

            # Create the lead
            lead = self.env['crm.lead'].sudo().create({
                'name': name,
                'contact_name': name,
                'email_from': email,
                'phone': phone,
                'description': 'Lead from Facebook',
                'stage_id': stage.id,  # Assign the stage ID
                'partner_id': customer.id,  # Link the customer
            })

            _logger.info(f"Lead created with ID: {lead.id}")

        except Exception as e:
            _logger.error(f"Error processing Facebook lead: {str(e)}")


# Cron job definition to poll Facebook leads every hour
class IrCron(models.Model):
    _inherit = 'ir.cron'

    @api.model
    def create_cron_job(self):
        # Create or update the cron job
        cron = self.env.ref('your_module_name.poll_facebook_leads_cron', raise_if_not_found=False)
        if not cron:
            self.env['ir.cron'].create({
                'name': 'Poll Facebook Leads',
                'model_id': self.env.ref('your_module_name.model_lead_poller').id,
                'state': 'code',
                'code': 'model.poll_facebook_leads()',
                'active': True,
                'interval_number': 5,
                'interval_type': 'minutes',
            })
