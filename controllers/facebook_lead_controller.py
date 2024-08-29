from odoo import http
from odoo.http import request
import json
import logging
import requests

_logger = logging.getLogger(__name__)


class FacebookLeadController(http.Controller):
    @http.route('/webhook/facebook', type='json', auth='public', methods=['POST'], csrf=False)
    def facebook_webhook(self, **kwargs):
        _logger.info("Facebook Lead Webhook Received")

        try:
            # Extract data from the incoming request
            data = request.jsonrequest
            _logger.info(f"Received data: {json.dumps(data)}")

            # Process each lead
            for entry in data.get('entry', []):
                for lead_data in entry.get('changes', []):
                    if lead_data.get('field') == 'leadgen':
                        lead_id = lead_data['value']['leadgen_id']

                        # Fetch the lead details using Facebook's Graph API
                        lead_details = self.fetch_facebook_lead(lead_id)

                        # Extract relevant information
                        name = lead_details.get('full_name')  # Assuming Facebook provides this key
                        email = lead_details.get('email')
                        phone = lead_details.get('phone_number')
                        stage_name = 'facebook'  # Example: hardcoded or can be extracted if available

                        # Ensure all required fields are provided
                        if not all([name, email, phone, stage_name]):
                            _logger.warning("Missing required fields")
                            continue

                        # Find the stage ID based on the stage name
                        stage = request.env['crm.stage'].sudo().search([('name', '=', stage_name)], limit=1)
                        if not stage:
                            _logger.warning(f"Stage '{stage_name}' not found")
                            continue

                        # Check if customer exists
                        customer = request.env['res.partner'].sudo().search([('name', '=', name)], limit=1)
                        if not customer:
                            # Create a new customer if it doesn't exist
                            customer = request.env['res.partner'].sudo().create({
                                'name': name,
                                'email': email,
                                'phone': phone,
                            })

                        # Create the lead
                        lead = request.env['crm.lead'].sudo().create({
                            'name': name,
                            'contact_name': name,
                            'email_from': email,
                            'phone': phone,
                            'description': 'Lead from Facebook',
                            'stage_id': stage.id,  # Assign the stage ID
                            'partner_id': customer.id,  # Link the customer
                        })

                        _logger.info(f"Lead created with ID: {lead.id}")

            return json.dumps({'status': 'success'})

        except Exception as e:
            _logger.error(f"Error processing Facebook lead: {str(e)}")
            return json.dumps({'status': 'error', 'message': str(e)})

    def fetch_facebook_lead(self, lead_id):
        # Use the Facebook Graph API to fetch lead details
        access_token = 'EAAROiwO311kBO8ITFiVFWf0rfyYt8IajXWWhJcgwoWo5fkYZBr6kB74Au3elSVHZC1ivfXqpS8mbUj8VeuCydRlXCancAT82vcDgaogGcrxi9XkZAulXQNTZAeyhgMOYcR9VtfBKDC1HKLe0EA9HoOHJ48EZCK3gyZAr7ZBMhcvJkGNpnqzaNeGZB8q0yffAZBTazrLMefv8yWkaWnoshPNq4eaYYmyYkNUUJ4sj0DhEEMM8bYGfWdFMyWyfVTsI91AZDZD'
        graph_url = f"https://graph.facebook.com/v11.0/{lead_id}?access_token={access_token}"

        # Make an HTTP request to fetch lead details
        response = requests.get(graph_url)
        return response.json()
