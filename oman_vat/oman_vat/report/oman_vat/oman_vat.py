# Copyright (c) 2022, ERPGulf and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_url_to_list
import json

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "title",
            "label": _("Title"),
            "fieldtype": "Data",
            "width": 300
        },
        {
            "fieldname": "amount",
            "label": _("Amount (OMR)"),
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "fieldname": "adjustment_amount",
            "label": _("Adjustment (OMR)"),
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "fieldname": "vat_amount",
            "label": _("VAT Amount (OMR)"),
            "fieldtype": "Currency",
            "width": 150,
        }
    ]

def get_data(filters):
    data = []
    company = filters.get('company')
    
    if not company:
        return data

    # Validate if OMAN VAT settings exist
    if not frappe.db.exists('OMAN VAT Setting', company):
        url = get_url_to_list('OMAN VAT Setting')
        frappe.msgprint(_('Please create <a href="{0}">OMAN VAT Setting</a> for {1}').format(url, company))
        return data

    oman_vat_setting = frappe.get_doc('OMAN VAT Setting', company)
    
    # --- SALES SECTION ---
    append_data(data, '<b>VAT on Sales</b>', '', '', '')
    
    sales_total_taxable = 0
    sales_total_adjustment = 0
    sales_total_vat = 0

    for vat_setting in oman_vat_setting.oman_vat_sales_accounts:
        taxable, adjustment, vat = get_tax_data_for_each_vat_setting(vat_setting, filters, 'Sales Invoice')
        
        append_data(data, vat_setting.title, taxable, adjustment, vat)
        
        sales_total_taxable += taxable
        sales_total_adjustment += adjustment
        sales_total_vat += vat

    append_data(data, '<b>Total Sales</b>', sales_total_taxable, sales_total_adjustment, sales_total_vat)
    append_data(data, '', '', '', '') # Spacer

    # --- PURCHASE SECTION ---
    append_data(data, '<b>VAT on Purchases</b>', '', '', '')
    
    pur_total_taxable = 0
    pur_total_adjustment = 0
    pur_total_vat = 0

    for vat_setting in oman_vat_setting.oman_vat_purchase_accounts:
        taxable, adjustment, vat = get_tax_data_for_each_vat_setting(vat_setting, filters, 'Purchase Invoice')
        
        append_data(data, vat_setting.title, taxable, adjustment, vat)
        
        pur_total_taxable += taxable
        pur_total_adjustment += adjustment
        pur_total_vat += vat

    append_data(data, '<b>Total Purchases</b>', pur_total_taxable, pur_total_adjustment, pur_total_vat)

    return data

def get_tax_data_for_each_vat_setting(vat_setting, filters, doctype):
    from_date = filters.get('from_date')
    to_date = filters.get('to_date')

    total_taxable_amount = 0
    total_taxable_adjustment_amount = 0
    total_tax = 0

    # Fetch Invoices within date range
    invoices = frappe.get_list(doctype, 
        filters={
            'docstatus': 1,
            'company': filters.get('company'),
            'posting_date': ['between', [from_date, to_date]]
        }, 
        fields=['name', 'is_return']
    )

    for inv in invoices:
        # Get items that match the specific Item Tax Template
        items = frappe.get_all(f'{doctype} Item', 
            filters={
                'parent': inv.name,
                'item_tax_template': vat_setting.item_tax_template
            }, 
            fields=['item_code', 'net_amount']
        )

        for item in items:
            # Handle standard vs return amounts
            if inv.is_return == 0:
                total_taxable_amount += item.net_amount
            else:
                total_taxable_adjustment_amount += item.net_amount

            # Get exact VAT for this specific item from the tax table
            total_tax += get_tax_amount(item.item_code, vat_setting.account, doctype, inv.name)
        
    return total_taxable_amount, total_taxable_adjustment_amount, total_tax

def get_tax_amount(item_code, account_head, doctype, parent):
    tax_doctype = 'Sales Taxes and Charges' if doctype == 'Sales Invoice' else 'Purchase Taxes and Charges'
    
    # We fetch all tax rows because the account name in the invoice 
    # might have a company suffix (e.g., " - AFLL") or different spacing
    tax_rows = frappe.get_all(tax_doctype, 
        filters={'parent': parent}, 
        fields=['account_head', 'item_wise_tax_detail']
    )

    tax_amount = 0
    clean_setting_account = account_head.strip().lower()

    for row in tax_rows:
        clean_row_account = row.account_head.strip().lower()
        
        # Check if the setting account matches the row account (partial match to ignore suffixes)
        if clean_setting_account in clean_row_account:
            if row.item_wise_tax_detail:
                details = json.loads(row.item_wise_tax_detail)
                if item_code in details:
                    # Index 1 is the calculated tax amount
                    tax_amount += details[item_code][1]
                    # We don't break here in case there are multiple tax rows for the same account
    
    return tax_amount

def append_data(data, title, amount, adjustment_amount, vat_amount):
    data.append({
        "title": title, 
        "amount": amount, 
        "adjustment_amount": adjustment_amount, 
        "vat_amount": vat_amount
    })


# --------Earlier-------------
# # Copyright (c) 2022, ERPGulf and contributors
# # For license information, please see license.txt

# from __future__ import unicode_literals
# import frappe
# from frappe import _
# from frappe.utils import get_url_to_list
# from erpnext.controllers.taxes_and_totals import get_itemised_tax_breakup_data, get_rounded_tax_amount
# import json

# def execute(filters=None):
# 	columns = columns = get_columns()
# 	data = get_data(filters)
# 	return columns, data

# def get_columns():
# 	return [
# 		{
# 			"fieldname": "title",
# 			"label": _("Title"),
# 			"fieldtype": "Data",
# 			"width": 300
# 		},
# 		{
# 			"fieldname": "amount",
# 			"label": _("Amount (OMR)"),
# 			"fieldtype": "Currency",
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "adjustment_amount",
# 			"label": _("Adjustment (OMR)"),
# 			"fieldtype": "Currency",
# 			"width": 150,
# 		},
# 		{
# 			"fieldname": "vat_amount",
# 			"label": _("VAT Amount (OMR)"),
# 			"fieldtype": "Currency",
# 			"width": 150,
# 		}
# 	]

# def get_data(filters):
# 	data = []

# 	# Validate if vat settings exist
# 	company = filters.get('company')
# 	if frappe.db.exists('OMAN VAT Setting', company) is None:
# 		url = get_url_to_list('OMAN VAT Setting')
# 		frappe.msgprint(f'Create <a href="{url}">OMAN VAT Setting</a> for this company')
# 		return data

# 	oman_vat_setting = frappe.get_doc('OMAN VAT Setting', company)
	
# 	# Sales Heading
# 	append_data(data, 'VAT on Sales', '', '', '')

# 	grand_total_taxable_amount = 0
# 	grand_total_taxable_adjustment_amount = 0
# 	grand_total_tax = 0

# 	for vat_setting in oman_vat_setting.oman_vat_sales_accounts:
# 		total_taxable_amount, total_taxable_adjustment_amount, \
# 			total_tax = get_tax_data_for_each_vat_setting(vat_setting, filters, 'Sales Invoice')
		
# 		# Adding results to data
# 		append_data(data, vat_setting.title, total_taxable_amount, 
# 			total_taxable_adjustment_amount, total_tax)
		
# 		grand_total_taxable_amount += total_taxable_amount
# 		grand_total_taxable_adjustment_amount += total_taxable_adjustment_amount
# 		grand_total_tax += total_tax

# 	# Sales Grand Total
# 	append_data(data, 'Grand Total', grand_total_taxable_amount, 
# 		grand_total_taxable_adjustment_amount, grand_total_tax )
	
# 	# Blank Line
# 	append_data(data, '', '', '', '')

# 	# Purchase Heading
# 	append_data(data, 'VAT on Purchases', '', '', '')

# 	grand_total_taxable_amount = 0
# 	grand_total_taxable_adjustment_amount = 0
# 	grand_total_tax = 0

# 	for vat_setting in oman_vat_setting.oman_vat_purchase_accounts:
# 		total_taxable_amount, total_taxable_adjustment_amount, \
# 			total_tax = get_tax_data_for_each_vat_setting(vat_setting, filters, 'Purchase Invoice')
		
# 		# Adding results to data
# 		append_data(data, vat_setting.title, total_taxable_amount, 
# 			total_taxable_adjustment_amount, total_tax)

# 		grand_total_taxable_amount += total_taxable_amount
# 		grand_total_taxable_adjustment_amount += total_taxable_adjustment_amount
# 		grand_total_tax += total_tax

# 	# Purchase Grand Total
# 	append_data(data, 'Grand Total', grand_total_taxable_amount, 
# 		grand_total_taxable_adjustment_amount, grand_total_tax )

# 	return data

# def get_tax_data_for_each_vat_setting(vat_setting, filters, doctype):
# 	'''
# 	(OMAN, {filters}, 'Sales Invoice') => 500, 153, 10 \n
# 	calculates and returns \n
# 	total_taxable_amount, total_taxable_adjustment_amount, total_tax'''
# 	from_date = filters.get('from_date')
# 	to_date = filters.get('to_date')

# 	# Initiate variables
# 	total_taxable_amount = 0
# 	total_taxable_adjustment_amount = 0
# 	total_tax = 0
# 	# Fetch All Invoices
# 	invoices = frappe.get_list(doctype, 
# 	filters ={
# 		'docstatus': 1,
# 		'posting_date': ['between', [from_date, to_date]]
# 	}, 
# 	fields =['name', 'is_return'])

# 	for invoice in invoices:
# 		invoice_items = frappe.get_list(f'{doctype} Item', 
# 		filters ={
# 			'docstatus': 1,
# 			'parent': invoice.name,
# 			'item_tax_template': vat_setting.item_tax_template
# 		}, 
# 		fields =['item_code', 'net_amount'])

		
# 		for item in invoice_items:
# 			# Summing up total taxable amount
# 			if invoice.is_return == 0:
# 				total_taxable_amount += item.net_amount
			
# 			if invoice.is_return == 1:
# 				total_taxable_adjustment_amount += item.net_amount

# 			# Summing up total tax
# 			total_tax += get_tax_amount(item.item_code, vat_setting.account, doctype, invoice.name)
		
# 	return total_taxable_amount, total_taxable_adjustment_amount, total_tax
		


# def append_data(data, title, amount, adjustment_amount, vat_amount):
# 	"""Returns data with appended value."""
# 	data.append({"title":title, "amount": amount, "adjustment_amount": adjustment_amount, "vat_amount": vat_amount})

# def get_tax_amount(item_code, account_head, doctype, parent):
# 	if doctype == 'Sales Invoice':
# 		tax_doctype = 'Sales Taxes and Charges'
	
# 	elif doctype == 'Purchase Invoice':
# 		tax_doctype = 'Purchase Taxes and Charges'
	
# 	item_wise_tax_detail = frappe.get_value(tax_doctype, {
# 		'docstatus': 1,
# 		'parent': parent,
# 		'account_head': account_head
# 	}, 'item_wise_tax_detail')

# 	tax_amount = 0
# 	if item_wise_tax_detail and len(item_wise_tax_detail) > 0:
# 		item_wise_tax_detail = json.loads(item_wise_tax_detail)
# 		for key, value in item_wise_tax_detail.items():
# 			if key == item_code:
# 				tax_amount = value[1]
# 				break
	
# 	return tax_amount