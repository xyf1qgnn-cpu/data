"""
安全存储管理器 - 处理API密钥的加密存储
支持Windows Credential Manager和加密配置文件
"""

import os
import json
import base64
import hashlib
import logging
from typing import Dict, Optional, Any
import platform

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


class SecureStorage:
    """安全存储管理器，处理API密钥加密存储"""

    SERVICE_NAME = "CFST_Data_Extractor"
    KEY_NAME = "api_key"

    def __init__(self):
        """初始化安全存储"""
        self.keyring_available = KEYRING_AVAILABLE
        self.cryptography_available = CRYPTOGRAPHY_AVAILABLE
        self.crypto_key = None
        self.logger = logging.getLogger(__name__)

        if self.cryptography_available:
            self.crypto_key = self.generate_crypto_key()

    def generate_crypto_key(self) -> bytes:
        """
        生成加密密钥

        Returns:
            加密密钥字节
        """
        try:
            # 基于系统信息生成唯一密钥种子
            system_info = {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "node": platform.node(),
                "processor": platform.processor()
            }

            # 使用系统信息和用户信息生成种子
            seed = json.dumps(system_info, sort_keys=True).encode()

            # 生成确定性密钥（相同系统生成相同密钥）
            key = hashlib.sha256(seed).digest()
            return key

        except Exception as e:
            self.logger.error(f"生成加密密钥失败: {e}")
            # 回退到固定密钥（安全性较低）
            return b"cfst_data_extractor_default_key_2026"

    def encrypt_api_key(self, api_key: str) -> Optional[Dict[str, str]]:
        """
        加密API密钥

        Args:
            api_key: 原始API密钥

        Returns:
            加密数据字典，包含加密数据和salt
        """
        if not api_key or not self.cryptography_available:
            return None

        try:
            # 生成随机salt
            salt = os.urandom(16)

            # 使用PBKDF2派生密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(self.crypto_key))

            # 创建Fernet加密器
            f = Fernet(derived_key)

            # 加密API密钥
            encrypted = f.encrypt(api_key.encode())

            # 返回加密数据和salt
            return {
                'encrypted': base64.b64encode(encrypted).decode(),
                'salt': base64.b64encode(salt).decode(),
                'version': '1.0'
            }

        except Exception as e:
            self.logger.error(f"加密API密钥失败: {e}")
            return None

    def decrypt_api_key(self, encrypted_data: Dict[str, str]) -> Optional[str]:
        """
        解密API密钥

        Args:
            encrypted_data: 加密数据字典

        Returns:
            解密后的API密钥
        """
        if not encrypted_data or not self.cryptography_available:
            return None

        try:
            # 提取加密数据和salt
            encrypted = base64.b64decode(encrypted_data['encrypted'])
            salt = base64.b64decode(encrypted_data['salt'])

            # 使用PBKDF2派生相同的密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            derived_key = base64.urlsafe_b64encode(kdf.derive(self.crypto_key))

            # 创建Fernet解密器
            f = Fernet(derived_key)

            # 解密API密钥
            decrypted = f.decrypt(encrypted)
            return decrypted.decode()

        except Exception as e:
            self.logger.error(f"解密API密钥失败: {e}")
            return None

    def save_api_key(self, api_key: str, use_keyring: bool = True) -> bool:
        """
        保存API密钥到安全存储

        Args:
            api_key: API密钥
            use_keyring: 是否使用keyring（Windows Credential Manager）

        Returns:
            是否成功保存
        """
        if not api_key:
            self.logger.warning("尝试保存空的API密钥")
            return False

        try:
            # 加密API密钥
            encrypted_data = self.encrypt_api_key(api_key)
            if not encrypted_data:
                self.logger.error("API密钥加密失败")
                return False

            # 转换为JSON字符串
            encrypted_json = json.dumps(encrypted_data)

            # 优先使用keyring（Windows Credential Manager）
            if use_keyring and self.keyring_available:
                try:
                    keyring.set_password(
                        self.SERVICE_NAME,
                        self.KEY_NAME,
                        encrypted_json
                    )
                    self.logger.info("API密钥已保存到Windows Credential Manager")
                    return True
                except Exception as e:
                    self.logger.warning(f"保存到keyring失败，回退到配置文件: {e}")

            # 回退到加密配置文件
            return self.save_to_config_file(encrypted_json)

        except Exception as e:
            self.logger.error(f"保存API密钥失败: {e}")
            return False

    def load_api_key(self, use_keyring: bool = True) -> Optional[str]:
        """
        从安全存储加载API密钥

        Args:
            use_keyring: 是否使用keyring（Windows Credential Manager）

        Returns:
            API密钥，如果加载失败则返回None
        """
        try:
            encrypted_json = None

            # 优先从keyring加载
            if use_keyring and self.keyring_available:
                try:
                    encrypted_json = keyring.get_password(
                        self.SERVICE_NAME,
                        self.KEY_NAME
                    )
                    if encrypted_json:
                        self.logger.info("从Windows Credential Manager加载API密钥")
                except Exception as e:
                    self.logger.warning(f"从keyring加载失败: {e}")

            # 如果keyring没有，尝试从配置文件加载
            if not encrypted_json:
                encrypted_json = self.load_from_config_file()

            if not encrypted_json:
                self.logger.info("未找到保存的API密钥")
                return None

            # 解析加密数据
            encrypted_data = json.loads(encrypted_json)

            # 解密API密钥
            api_key = self.decrypt_api_key(encrypted_data)
            if api_key:
                self.logger.info("API密钥加载成功")
                return api_key
            else:
                self.logger.error("API密钥解密失败")
                return None

        except json.JSONDecodeError as e:
            self.logger.error(f"解析加密数据失败: {e}")
            return None
        except Exception as e:
            self.logger.error(f"加载API密钥失败: {e}")
            return None

    def delete_api_key(self, use_keyring: bool = True) -> bool:
        """
        删除保存的API密钥

        Args:
            use_keyring: 是否删除keyring中的密钥

        Returns:
            是否成功删除
        """
        success = True

        # 删除keyring中的密钥
        if use_keyring and self.keyring_available:
            try:
                keyring.delete_password(self.SERVICE_NAME, self.KEY_NAME)
                self.logger.info("从Windows Credential Manager删除API密钥")
            except keyring.errors.PasswordDeleteError:
                # 密钥不存在，不算错误
                pass
            except Exception as e:
                self.logger.error(f"从keyring删除密钥失败: {e}")
                success = False

        # 删除配置文件中的密钥
        config_deleted = self.delete_from_config_file()
        if not config_deleted:
            success = False

        return success

    def save_to_config_file(self, encrypted_json: str) -> bool:
        """
        保存加密数据到配置文件

        Args:
            encrypted_json: 加密的JSON数据

        Returns:
            是否成功保存
        """
        try:
            # 这里需要与ConfigManager集成
            # 暂时使用独立文件
            config_path = "secure_config.json"
            config_data = {
                "api_key": encrypted_json,
                "encrypted": True,
                "version": "1.0"
            }

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)

            # 设置文件权限（仅限Unix系统）
            if platform.system() != "Windows":
                os.chmod(config_path, 0o600)

            self.logger.info(f"API密钥已保存到配置文件: {config_path}")
            return True

        except Exception as e:
            self.logger.error(f"保存到配置文件失败: {e}")
            return False

    def load_from_config_file(self) -> Optional[str]:
        """
        从配置文件加载加密数据

        Returns:
            加密的JSON数据
        """
        try:
            config_path = "secure_config.json"
            if not os.path.exists(config_path):
                return None

            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            if config_data.get("encrypted", False):
                return config_data.get("api_key")
            else:
                self.logger.warning("配置文件中的API密钥未加密")
                return None

        except Exception as e:
            self.logger.error(f"从配置文件加载失败: {e}")
            return None

    def delete_from_config_file(self) -> bool:
        """
        从配置文件删除加密数据

        Returns:
            是否成功删除
        """
        try:
            config_path = "secure_config.json"
            if os.path.exists(config_path):
                os.remove(config_path)
                self.logger.info(f"已删除配置文件: {config_path}")
            return True
        except Exception as e:
            self.logger.error(f"删除配置文件失败: {e}")
            return False

    def test_api_key(self, api_key: str) -> bool:
        """
        测试API密钥是否有效

        Args:
            api_key: API密钥

        Returns:
            是否有效
        """
        if not api_key:
            return False

        try:
            # 简单的格式检查
            # DeepSeek API密钥通常是sk-开头的字符串
            if api_key.startswith("sk-") and len(api_key) > 20:
                return True
            else:
                self.logger.warning("API密钥格式不正确")
                return False

        except Exception as e:
            self.logger.error(f"测试API密钥失败: {e}")
            return False

    def get_storage_info(self) -> Dict[str, Any]:
        """
        获取存储信息

        Returns:
            存储信息字典
        """
        info = {
            "keyring_available": self.keyring_available,
            "cryptography_available": self.cryptography_available,
            "platform": platform.system(),
            "service_name": self.SERVICE_NAME,
            "key_name": self.KEY_NAME
        }

        # 检查是否有保存的密钥
        try:
            api_key = self.load_api_key()
            info["has_saved_key"] = api_key is not None
            info["key_length"] = len(api_key) if api_key else 0
        except Exception:
            info["has_saved_key"] = False
            info["key_length"] = 0

        return info

    def clear_all_storage(self) -> bool:
        """
        清除所有存储的密钥

        Returns:
            是否成功清除
        """
        success = True

        # 删除keyring中的密钥
        if self.keyring_available:
            try:
                keyring.delete_password(self.SERVICE_NAME, self.KEY_NAME)
            except keyring.errors.PasswordDeleteError:
                # 密钥不存在，不算错误
                pass
            except Exception as e:
                self.logger.error(f"清除keyring存储失败: {e}")
                success = False

        # 删除配置文件
        config_deleted = self.delete_from_config_file()
        if not config_deleted:
            success = False

        if success:
            self.logger.info("所有存储的API密钥已清除")
        else:
            self.logger.warning("清除API密钥存储时出现部分错误")

        return success