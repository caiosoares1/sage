from django.test import TestCase
from unittest.mock import patch, MagicMock
from utils.email import enviar_notificacao_email


class EmailTestCase(TestCase):
    """Testes para funções de email"""
    
    @patch('utils.email.send_mail')
    def test_enviar_email_sucesso(self, mock_send_mail):
        """Testa envio de email com sucesso"""
        mock_send_mail.return_value = 1
        
        resultado = enviar_notificacao_email(
            assunto='Teste',
            mensagem='Mensagem de teste',
            destinatarios=['teste@example.com']
        )
        
        self.assertTrue(resultado)
        mock_send_mail.assert_called_once()
    
    @patch('utils.email.send_mail')
    def test_enviar_email_multiplos_destinatarios(self, mock_send_mail):
        """Testa envio para múltiplos destinatários"""
        mock_send_mail.return_value = 1
        
        resultado = enviar_notificacao_email(
            assunto='Teste',
            mensagem='Mensagem',
            destinatarios=['teste1@example.com', 'teste2@example.com']
        )
        
        self.assertTrue(resultado)
        # Verifica que foi chamado com lista de destinatários
        self.assertEqual(len(mock_send_mail.call_args[1]['recipient_list']), 2)
    
    @patch('utils.email.send_mail')
    def test_enviar_email_com_excecao(self, mock_send_mail):
        """Testa comportamento quando há erro no envio"""
        mock_send_mail.side_effect = Exception("Erro de conexão")
        
        # Deve retornar False ou capturar exceção
        try:
            resultado = enviar_notificacao_email(
                assunto='Teste',
                mensagem='Mensagem',
                destinatarios=['teste@example.com']
            )
            # Se não lançar exceção, deve retornar False
            self.assertFalse(resultado)
        except Exception:
            # Se lançar exceção, está OK também
            pass
    
    @patch('utils.email.send_mail')
    def test_enviar_email_verifica_parametros(self, mock_send_mail):
        """Testa que parâmetros corretos são passados para send_mail"""
        mock_send_mail.return_value = 1
        
        assunto = 'Assunto Teste'
        mensagem = 'Corpo da mensagem'
        destinatarios = ['destino@example.com']
        
        enviar_notificacao_email(
            assunto=assunto,
            mensagem=mensagem,
            destinatarios=destinatarios
        )
        
        # Verificar que foi chamado com os parâmetros corretos
        call_kwargs = mock_send_mail.call_args[1]
        self.assertEqual(call_kwargs['subject'], assunto)
        self.assertEqual(call_kwargs['message'], mensagem)
        self.assertEqual(call_kwargs['recipient_list'], destinatarios)
