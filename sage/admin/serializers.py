"""
Serializers para a API REST do módulo admin.
Responsável pela serialização de Empresa e Supervisor.
"""
import re
from rest_framework import serializers
from .models import Empresa, Supervisor
from users.models import Usuario


def validar_cnpj(cnpj):
    """
    Valida um CNPJ (apenas dígitos, deve ter 14 caracteres).
    Retorna True se válido, False caso contrário.
    """
    # Remove caracteres não numéricos
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    
    # Verifica se tem 14 dígitos
    if len(cnpj) != 14:
        return False
    
    # Verifica se todos os dígitos são iguais (CNPJs inválidos como 00000000000000)
    if cnpj == cnpj[0] * 14:
        return False
    
    return True


class EmpresaSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Empresa.
    CA1 - Valida campos obrigatórios: CNPJ, rua, número, bairro e razão social
    """
    supervisores_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Empresa
        fields = ['id', 'cnpj', 'razao_social', 'rua', 'numero', 'bairro', 'supervisores_count']
        read_only_fields = ['id']
    
    def get_supervisores_count(self, obj):
        """Retorna a quantidade de supervisores vinculados à empresa"""
        return obj.supervisor_set.count()
    
    def validate_cnpj(self, value):
        """Valida o CNPJ"""
        # Remove caracteres não numéricos
        cnpj_limpo = re.sub(r'[^0-9]', '', value)
        
        if not cnpj_limpo:
            raise serializers.ValidationError('CNPJ é obrigatório.')
        
        if not validar_cnpj(cnpj_limpo):
            raise serializers.ValidationError('CNPJ inválido. Deve conter 14 dígitos numéricos.')
        
        # Verifica duplicidade (exceto na edição do mesmo registro)
        queryset = Empresa.objects.filter(cnpj=cnpj_limpo)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError('Já existe uma empresa cadastrada com este CNPJ.')
        
        return cnpj_limpo
    
    def validate_numero(self, value):
        """Valida que o número é positivo"""
        if value is not None and value <= 0:
            raise serializers.ValidationError('Número deve ser um valor positivo.')
        return value
    
    def validate_razao_social(self, value):
        """Valida a razão social"""
        if not value or not value.strip():
            raise serializers.ValidationError('Razão Social é obrigatória.')
        return value.strip()
    
    def validate_rua(self, value):
        """Valida a rua"""
        if not value or not value.strip():
            raise serializers.ValidationError('Rua é obrigatória.')
        return value.strip()
    
    def validate_bairro(self, value):
        """Valida o bairro"""
        if not value or not value.strip():
            raise serializers.ValidationError('Bairro é obrigatório.')
        return value.strip()


class EmpresaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de empresas.
    """
    supervisores_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Empresa
        fields = ['id', 'cnpj', 'razao_social', 'supervisores_count']
    
    def get_supervisores_count(self, obj):
        """Retorna a quantidade de supervisores vinculados à empresa"""
        return obj.supervisor_set.count()


class SupervisorSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Supervisor.
    CA2 - Supervisor vinculado corretamente a uma empresa
    CA3 - Valida campos obrigatórios: Nome, Cargo, Empresa
    """
    empresa_nome = serializers.CharField(source='empresa.razao_social', read_only=True)
    email = serializers.EmailField(write_only=True, required=True)
    senha = serializers.CharField(write_only=True, required=True, min_length=6)
    
    class Meta:
        model = Supervisor
        fields = ['id', 'nome', 'contato', 'cargo', 'empresa', 'empresa_nome', 'email', 'senha']
        read_only_fields = ['id']
    
    def validate_email(self, value):
        """Valida que o email não está duplicado"""
        if not value:
            raise serializers.ValidationError('Email é obrigatório.')
        
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError('Já existe um usuário cadastrado com este email.')
        
        return value
    
    def validate_nome(self, value):
        """Valida o nome"""
        if not value or not value.strip():
            raise serializers.ValidationError('Nome é obrigatório.')
        return value.strip()
    
    def validate_cargo(self, value):
        """Valida o cargo"""
        if not value or not value.strip():
            raise serializers.ValidationError('Cargo é obrigatório.')
        return value.strip()
    
    def validate_empresa(self, value):
        """Valida a empresa"""
        if not value:
            raise serializers.ValidationError('Empresa é obrigatória.')
        return value
    
    def validate_senha(self, value):
        """Valida a senha"""
        if not value or len(value) < 6:
            raise serializers.ValidationError('Senha deve ter pelo menos 6 caracteres.')
        return value
    
    def create(self, validated_data):
        """Cria o supervisor e o usuário associado"""
        email = validated_data.pop('email')
        senha = validated_data.pop('senha')
        
        # Cria o usuário
        usuario = Usuario.objects.create_user(
            username=email,
            email=email,
            password=senha,
            tipo='supervisor'
        )
        
        # Cria o supervisor
        supervisor = Supervisor.objects.create(
            usuario=usuario,
            **validated_data
        )
        
        return supervisor


class SupervisorUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de Supervisor (sem campos de usuário).
    CA3 - Valida campos obrigatórios: Nome, Cargo, Empresa
    """
    empresa_nome = serializers.CharField(source='empresa.razao_social', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)
    
    class Meta:
        model = Supervisor
        fields = ['id', 'nome', 'contato', 'cargo', 'empresa', 'empresa_nome', 'email']
        read_only_fields = ['id', 'email']
    
    def validate_nome(self, value):
        """Valida o nome"""
        if not value or not value.strip():
            raise serializers.ValidationError('Nome é obrigatório.')
        return value.strip()
    
    def validate_cargo(self, value):
        """Valida o cargo"""
        if not value or not value.strip():
            raise serializers.ValidationError('Cargo é obrigatório.')
        return value.strip()
    
    def validate_empresa(self, value):
        """Valida a empresa"""
        if not value:
            raise serializers.ValidationError('Empresa é obrigatória.')
        return value


class SupervisorListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listagem de supervisores.
    """
    empresa_nome = serializers.CharField(source='empresa.razao_social', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)
    
    class Meta:
        model = Supervisor
        fields = ['id', 'nome', 'cargo', 'empresa', 'empresa_nome', 'email']


class SupervisorDetailSerializer(serializers.ModelSerializer):
    """
    Serializer detalhado para visualização de um supervisor.
    Inclui informações da empresa e do usuário.
    """
    empresa_nome = serializers.CharField(source='empresa.razao_social', read_only=True)
    empresa_cnpj = serializers.CharField(source='empresa.cnpj', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)
    estagios_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Supervisor
        fields = [
            'id', 'nome', 'contato', 'cargo', 
            'empresa', 'empresa_nome', 'empresa_cnpj',
            'email', 'estagios_count'
        ]
    
    def get_estagios_count(self, obj):
        """Retorna a quantidade de estágios supervisionados"""
        from estagio.models import Estagio
        return Estagio.objects.filter(supervisor=obj).count()
